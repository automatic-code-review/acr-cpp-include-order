import unittest
from html import escape

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
