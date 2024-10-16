import re

import automatic_code_review_commons as commons


def remove_duplicate_include(includes):
    retorno = []

    for include in includes:
        if include not in retorno:
            retorno.append(include)

    return retorno


def adjust_order(include_list, path, regex_order):
    include_list_ordered = []
    regex_order_copy = []
    regex_order_copy.extend(regex_order)

    if path.endswith(".cpp"):
        header_file = path.split("/")
        header_file = header_file[len(header_file) - 1]
        header_file = header_file.replace(".cpp", ".h")

        regex_order_copy.insert(0, {
            "orderType": "individual",
            "regex": [
                f"#include <{header_file}>",
                f"#include <.*/{header_file}>",
                f"#include \"{header_file}\"",
                f"#include \".*/{header_file}\"",
                f"#include \"ui_{header_file}\"",
            ]
        })

    for regex_obj in regex_order_copy:
        include_by_group = []

        for regex in regex_obj['regex']:
            not_add_list = []
            include_by_current = []

            for include in include_list:
                if re.match(regex, include):
                    include_by_current.append(f"{include}\n")
                else:
                    not_add_list.append(include)

            if regex_obj['orderType'] == 'individual':
                include_by_current.sort()

            include_by_group.extend(include_by_current)
            include_list = not_add_list

        if regex_obj['orderType'] == 'group':
            include_by_group.sort()

        include_list_ordered.extend(include_by_group)
        include_list_ordered.append("\n")

    return include_list_ordered


def remove_linhas_brancas_consecutivas(lista_strings):
    resultado = []
    linhas_em_branco = 0

    for linha in lista_strings:
        if linha.strip() == "":
            linhas_em_branco += 1
            if linhas_em_branco == 1:
                resultado.append(linha)
        else:
            linhas_em_branco = 0
            resultado.append(linha)

    return resultado


def check_order_changed(lines_changed, lines_original):
    lines_include_changed = []
    lines_include_original = []

    for line in lines_original:
        line = line.strip()

        if line.startswith("#include") and ".moc" not in line:
            lines_include_original.append(line)

    for line in lines_changed:
        line = line.strip()

        if line.startswith("#include") and ".moc" not in line:
            lines_include_changed.append(line)

    return lines_include_original != lines_include_changed


def get_start_comment(lines):
    lines_comment = []

    index = 0
    for line in lines:
        if line.startswith("//"):
            lines_comment.append(line)
            index += 1
            continue

        break

    return lines_comment, lines[index:]


def verify(path, regex_order):
    with open(path, 'r') as arquivo:
        lines = arquivo.readlines()

    lines_without_include = []
    lines_include = []
    lines_to_ignore, lines = get_start_comment(lines)

    if path.endswith(".h"):
        if "#pragma once" in lines[0]:
            lines_to_ignore.append(lines[0])
        else:
            header_file = path.split("/")
            header_file = header_file[len(header_file) - 1].upper()
            if "_p.h" in header_file:
                header_file = header_file.replace(".H", "_H")
                header_file = header_file.replace("_P", "PRIVATE")
            else:
                header_file = header_file.replace(".H", "_H")
                header_file = header_file.replace("-", "")

            lines_to_ignore.append(f"#ifndef {header_file}\n")
            lines_to_ignore.append(f"#define {header_file}\n")

    if path.endswith(".hpp"):
        header_file = path.split("/")
        header_file = header_file[len(header_file) - 1].upper()
        header_file = header_file.replace(".HPP", "_H")
        header_file = header_file.replace("-", "")
        lines_to_ignore.append(f"#ifndef {header_file}\n")
        lines_to_ignore.append(f"#define {header_file}\n")

    for line in lines:
        if line in lines_to_ignore:
            continue

        line_original = line
        line = line.strip()

        if line.startswith("#include") and ".moc" not in line:
            lines_include.append(line)
        else:
            lines_without_include.append(line_original)

    lines_include = remove_duplicate_include(lines_include)
    lines_include_ordered = adjust_order(lines_include, path, regex_order)

    linhas_fix = lines_to_ignore
    linhas_fix.append("\n")
    linhas_fix.extend(lines_include_ordered)
    linhas_fix.append("\n")
    linhas_fix.extend(lines_without_include)

    linhas_fix = remove_linhas_brancas_consecutivas(linhas_fix)

    if linhas_fix[0] == "\n":
        linhas_fix = linhas_fix[1:]

    lines_include_ordered = remove_linhas_brancas_consecutivas(lines_include_ordered)

    if check_order_changed(linhas_fix, lines):
        print(f'MUDOU ALGUMA ORDEM: {path}')
        return True, lines_include_ordered, linhas_fix

    return False, lines_include_ordered, linhas_fix


def ordered_to_string(ordered):
    strings = []
    for order in ordered:
        strings.append(f"- `{order}`")

    return "<br>".join(strings)


def review(config):
    regex_order = config['regexOrder']
    path_source = config['path_source']
    changes = config['merge']['changes']
    comment_description_pattern = config['message']

    comments = []

    for change in changes:
        if change['deleted_file']:
            continue

        new_path = change['new_path']
        full_path = path_source + "/" + new_path

        if not full_path.endswith(('.h', '.cpp', '.hpp', '.c')):
            continue

        changed, ordered, _ = verify(path=full_path, regex_order=regex_order)

        if not changed:
            continue

        comment_path = new_path
        comment_description = f"{comment_description_pattern}"
        comment_description = comment_description.replace("${FILE_PATH}", comment_path)
        comment_description = comment_description.replace("${ORDERED}", ordered_to_string(ordered))

        comments.append(commons.comment_create(
            comment_id=commons.comment_generate_id(comment_description),
            comment_path=comment_path,
            comment_description=comment_description,
            comment_snipset=False,
            comment_end_line=1,
            comment_start_line=1,
            comment_language=None,
        ))

    return comments
