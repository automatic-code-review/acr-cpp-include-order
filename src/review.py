import automatic_code_review_commons as commons
import re

def review(config):
    regex_order = config['regexOrder']
    path_source = config['path_source']
    changes = config['merge']['changes']
    comment_description = config['message']
    
    comments = []

    for change in changes:
        full_path = path_source + "/" + change['new_path']

        if full_path.endswith(('.h', '.cpp')):
            for comment in process_file(full_path, comment_description, path_source, regex_order):
                comments.append(comment)

    
    return comments

def get_include_list_ordered(include_list, full_path, regex_order):
    include_list_ordered = []

    if full_path.endswith(".cpp"):
        header_file = full_path.split("/")
        header_file = header_file[len(header_file)-1]
        header_file = header_file.replace(".cpp", ".h")
        regex_order.insert(0, f"#include \"{header_file}\"")
        regex_order.insert(0, f"#include \".*/{header_file}\"")

    for regex in regex_order:
        not_add_list = []

        for include in include_list:
            if re.match(regex, include):
                include_list_ordered.append(include)
            else:
                not_add_list.append(include)
        
        include_list = not_add_list

    return include_list_ordered;

def is_equals(first, second):
    if len(first) != len(second):
        return False
    
    max_index = len(first)-1
    for i in range(0, max_index):
        if first[i] != second[i]:
            return False
    
    return True


def ordered_to_string(ordered):
    strings = []
    for order in ordered:
        strings.append(f"- `{order}`")

    return "<br>".join(strings)


def process_file(full_path, comment_description_pattern, path_source, regex_order):
    comments = []
    include_list = []

    with open(full_path, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

        for linha in linhas:
            if re.match(r'^\s*#include\s*', linha):
                include = linha.replace("\n", "").strip()
                include_list.append(include)

    if len(include_list) > 0:
        ordered = get_include_list_ordered(include_list, full_path, regex_order)

        if not is_equals(include_list, ordered):
            comment_path = f"{full_path}".replace(path_source, "")[1:]
            comment_description=f"{comment_description_pattern}"
            comment_description = comment_description.replace("${FILE_PATH}", comment_path)
            comment_description = comment_description.replace("${ORDERED}", ordered_to_string(ordered))

            comments.append(commons.comment_create(
                comment_id=commons.comment_generate_id(comment_path),
                comment_path=comment_path,
                comment_description=comment_description,
                comment_snipset=False,
                comment_end_line=1,
                comment_start_line=1,
                comment_language=None,
            ))
    
    return comments
