import re


def modify_urdf(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    for line in lines:
        if line.strip().startswith('<limit'):
            modified_line = re.sub(r'(<limit)(.*?>)', r'\1 effort="30" velocity="1.0"\2', line)
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)

    with open(file_path, 'w') as file:
        file.writelines(modified_lines)


data_name = '100162'
modify_urdf(f'test_data/{data_name}/mobility.urdf')
