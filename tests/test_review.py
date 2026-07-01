import unittest
import tempfile
from pathlib import Path
from html import escape
from unittest import mock

import automatic_code_review_commons as commons
from src import review as review_module


def build_config(new_path):
    return {
        "regexOrder": [
            {
                "orderType": "group",
                "regex": [
                    r"#include <.*>",
                    r"#include \".*\"",
                ],
            }
        ],
        "path_source": "tests/fixtures",
        "merge": {
            "changes": [
                {
                    "deleted_file": False,
                    "new_path": new_path,
                }
            ],
        },
        "message": "Ordenacao incorreta em ${FILE_PATH}. Sugestao: ${ORDERED}",
    }


def to_expected_comment(comment_raw):
    return escape(comment_raw).replace("&lt;pre&gt;", "<pre>").replace("&lt;br&gt;", "<br>").replace("&lt;/pre&gt;", "</pre>")


class ReviewTests(unittest.TestCase):
    def assert_comment_payload(self, comment, expected_comment, expected_path):
        self.assertEqual(comment["id"], commons.comment_generate_id(expected_comment))
        self.assertEqual(comment["comment"], expected_comment)

        self.assertIn("position", comment)
        self.assertEqual(comment["position"]["language"], None)
        self.assertEqual(comment["position"]["path"], expected_path)
        self.assertEqual(comment["position"]["startInLine"], 1)
        self.assertEqual(comment["position"]["endInLine"], 1)
        self.assertEqual(comment["position"]["snipset"], False)

    def test_review_gera_comentario_com_config_valido(self):
        config = build_config(new_path="sample.cpp")

        comments = review_module.review(config)

        expected_comment_raw = (
            "Ordenacao incorreta em sample.cpp. Sugestao: "
            "<pre>#include <algorithm><br>#include <string><br>#include <vector><br></pre>"
        )
        expected_comment = to_expected_comment(expected_comment_raw)

        self.assertEqual(len(comments), 1)
        self.assert_comment_payload(comments[0], expected_comment, expected_path="sample.cpp")

    def test_review_nao_gera_comentario_quando_ordem_esta_correta(self):
        config = build_config(new_path="sample_ok.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_ignora_include_dentro_de_ifdef_linux(self):
        config = build_config(new_path="sample_ifdef_linux.cpp")

        comments = review_module.review(config)

        # Blocos condicionais devem ser preservados sem reordenar includes internos.
        self.assertEqual(comments, [])

    def test_review_ignora_include_dentro_de_elif(self):
        config = build_config(new_path="sample_if_elif_linux.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_ignora_include_dentro_de_else(self):
        config = build_config(new_path="sample_if_else_linux.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_remove_duplicate_include_remove_repetidos(self):
        includes = ["#include <a>", "#include <b>", "#include <a>"]

        deduplicados = review_module.remove_duplicate_include(includes)

        self.assertEqual(deduplicados, ["#include <a>", "#include <b>"])

    def test_adjust_order_para_header_nao_injeta_header_cpp(self):
        ordered = review_module.adjust_order(
            include_list=["#include <z>", "#include <a>"],
            path="sample.h",
            regex_order=[{"orderType": "group", "regex": [r"#include <.*>"]}],
        )

        self.assertEqual(ordered, ["#include <a>\n", "#include <z>\n", "\n"])

    def test_get_start_comment_sem_comentario_inicial(self):
        comments, remainder = review_module.get_start_comment(["#include <a>\n", "int main();\n"])

        self.assertEqual(comments, [])
        self.assertEqual(remainder, ["#include <a>\n", "int main();\n"])

    def test_verify_header_com_pragma_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "widget.h"
            file_path.write_text("#pragma once\n#include <a>\n", encoding="utf-8")

            changed, _, fixed = review_module.verify(
                path=str(file_path),
                regex_order=[{"orderType": "group", "regex": [r"#include <.*>"]}],
            )

            self.assertFalse(changed)
            self.assertIn("#pragma once\n", fixed)

    def test_verify_header_private_guard_para_p_h(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "widget_p.h"
            file_path.write_text("#include <z>\n", encoding="utf-8")

            _, _, fixed = review_module.verify(
                path=str(file_path),
                regex_order=[{"orderType": "group", "regex": [r"#include <.*>"]}],
            )

            self.assertEqual(fixed[0], "#ifndef WIDGET_P_H\n")
            self.assertEqual(fixed[1], "#define WIDGET_P_H\n")

    def test_verify_hpp_gera_include_guard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "my-widget.hpp"
            file_path.write_text("#include <z>\n", encoding="utf-8")

            _, _, fixed = review_module.verify(
                path=str(file_path),
                regex_order=[{"orderType": "group", "regex": [r"#include <.*>"]}],
            )

            self.assertEqual(fixed[0], "#ifndef MYWIDGET_H\n")
            self.assertEqual(fixed[1], "#define MYWIDGET_H\n")

    def test_verify_preserva_condicionais_aninhadas(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nested.cpp"
            file_path.write_text(
                "#if A\n"
                "#if B\n"
                "#include <z>\n"
                "#endif\n"
                "#endif\n"
                "#include <a>\n",
                encoding="utf-8",
            )

            changed, _, fixed = review_module.verify(
                path=str(file_path),
                regex_order=[{"orderType": "group", "regex": [r"#include <.*>"]}],
            )

            self.assertTrue(changed)
            self.assertIn("#if A\n", fixed)
            self.assertIn("#if B\n", fixed)
            self.assertIn("#include <z>\n", fixed)

    def test_verify_remove_linha_inicial_em_branco(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "blank.cpp"
            file_path.write_text("int a = 0;\n", encoding="utf-8")

            changed, _, fixed = review_module.verify(
                path=str(file_path),
                regex_order=[{"orderType": "group", "regex": [r"#include <.*>"]}],
            )

            self.assertFalse(changed)
            self.assertNotEqual(fixed[0], "\n")

    def test_review_ignora_deleted_file_e_extensao_invalida(self):
        config = {
            "regexOrder": [{"orderType": "group", "regex": [r"#include <.*>"]}],
            "path_source": "tests/fixtures",
            "merge": {
                "changes": [
                    {"deleted_file": True, "new_path": "sample.cpp"},
                    {"deleted_file": False, "new_path": "notes.txt"},
                ]
            },
            "message": "msg ${FILE_PATH} ${ORDERED}",
        }

        with mock.patch.object(review_module, "verify") as verify_mock:
            comments = review_module.review(config)

        verify_mock.assert_not_called()
        self.assertEqual(comments, [])
