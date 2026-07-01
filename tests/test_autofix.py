import unittest
import tempfile
from pathlib import Path
import sys
from unittest import mock


class AutofixImportTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.src_dir = self.repo_root / "src"
        sys.path.insert(0, str(self.src_dir))

    def tearDown(self):
        src_dir_str = str(self.src_dir)
        while src_dir_str in sys.path:
            sys.path.remove(src_dir_str)

    def test_import_autofix_module(self):
        from src import autofix as _autofix_module

        self.assertIsNotNone(_autofix_module)

    def test_autofix_lanca_excecao_para_extensao_invalida(self):
        from src import autofix as autofix_module

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invalid_path = temp_path / "arquivo.txt"

            invalid_path.write_text("conteudo", encoding="utf-8")

            with self.assertRaises(Exception) as context:
                autofix_module.autofix(path=str(invalid_path), config={"regexOrder": []})

            self.assertEqual(str(context.exception), "extension type not supported")

    def test_autofix_escreve_arquivo_quando_verify_indica_mudanca(self):
        from src import autofix as autofix_module

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cpp_path = temp_path / "arquivo.cpp"

            cpp_path.write_text("#include <z>\n", encoding="utf-8")

            import review

            config = {"regexOrder": [{"orderType": "group", "regex": ["#include <.*>"]}]}

            with mock.patch.object(review, "verify", return_value=(True, [], ["#include <a>\n"])) as verify_mock:
                changed = autofix_module.autofix(path=str(cpp_path), config=config)

            verify_mock.assert_called_once()
            self.assertTrue(changed)
            self.assertEqual(cpp_path.read_text(encoding="utf-8"), "#include <a>\n")

    def test_autofix_nao_escreve_arquivo_quando_sem_mudanca(self):
        from src import autofix as autofix_module

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cpp_path = temp_path / "arquivo.cpp"

            original = "#include <z>\n"
            cpp_path.write_text(original, encoding="utf-8")

            import review

            config = {"regexOrder": [{"orderType": "group", "regex": ["#include <.*>"]}]}

            with mock.patch.object(review, "verify", return_value=(False, [], ["#include <a>\n"])) as verify_mock:
                changed = autofix_module.autofix(path=str(cpp_path), config=config)

            verify_mock.assert_called_once()
            self.assertFalse(changed)
            self.assertEqual(cpp_path.read_text(encoding="utf-8"), original)

    def test_autofix_from_config_carrega_json_e_executa(self):
        from src import autofix as autofix_module

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cpp_path = temp_path / "arquivo.cpp"
            config_path = temp_path / "config.json"

            cpp_path.write_text("#include <z>\n", encoding="utf-8")
            config_path.write_text('{"regexOrder": [{"orderType": "group", "regex": ["#include <.*>"]}]}', encoding="utf-8")

            import review

            with mock.patch.object(review, "verify", return_value=(False, [], [])) as verify_mock:
                changed = autofix_module.autofix_from_config(path=str(cpp_path), config_path=str(config_path))

            verify_mock.assert_called_once()
            self.assertFalse(changed)

    def test_autofix_header_ordena_somente_includes_fora_de_ifdef(self):
        from src import autofix as autofix_module

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            header_path = temp_path / "myclass.h"

            header_path.write_text(
                "#ifdef MYCLASS_H\n"
                "#include \"zeta.h\"\n"
                "#ifdef __linux__\n"
                "#include <linux/input.h>\n"
                "#endif\n"
                "#include \"alpha.h\"\n"
                "#endif\n"
                "\n"
                "#include <vector>\n"
                "#include <algorithm>\n"
                "\n"
                "#ifndef FINAL\n"
                "int final_value = 1;\n"
                "#endif\n",
                encoding="utf-8",
            )

            config = {
                "regexOrder": [
                    {
                        "orderType": "group",
                        "regex": [
                            r"#include <.*>",
                            r"#include \".*\"",
                        ],
                    }
                ]
            }

            changed = autofix_module.autofix(path=str(header_path), config=config)

            self.assertTrue(changed)

            lines = header_path.read_text(encoding="utf-8").splitlines()

            self.assertIn("#ifndef MYCLASS_H", lines)
            self.assertIn("#define MYCLASS_H", lines)

            idx_algorithm = lines.index("#include <algorithm>")
            idx_vector = lines.index("#include <vector>")
            idx_ifdef_guard = lines.index("#ifdef MYCLASS_H")

            # Includes no escopo principal devem ser ordenados antes dos blocos condicionais.
            self.assertLess(idx_algorithm, idx_vector)
            self.assertLess(idx_vector, idx_ifdef_guard)

            # Includes dentro do condicional devem manter a ordem original.
            idx_zeta = lines.index("#include \"zeta.h\"")
            idx_linux = lines.index("#include <linux/input.h>")
            idx_alpha = lines.index("#include \"alpha.h\"")

            self.assertLess(idx_zeta, idx_linux)
            self.assertLess(idx_linux, idx_alpha)
