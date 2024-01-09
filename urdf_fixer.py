import re
import os
import argparse


# def modify_urdf(file_path):
#     with open(file_path, 'r') as file:
#         lines = file.readlines()

#     modified_lines = []
#     for line in lines:
#         if line.strip().startswith('<limit'):
#             modified_line = re.sub(r'(<limit)(.*?>)', r'\1 effort="30" velocity="1.0"\2', line)
#             modified_lines.append(modified_line)
#         else:
#             modified_lines.append(line)

#     with open(file_path, 'w') as file:
#         file.writelines(modified_lines)


def modify_urdf(file_path):
    try:
        with open(file_path, "r") as file:
            modified_lines = []
            for line in file:
                if line.strip().startswith("<limit"):
                    # Add 'effort' attribute if not present
                    if "effort=" not in line:
                        line = re.sub(r"(<limit)(.*?>)", r'\1 effort="30"\2', line)

                    # Add 'velocity' attribute if not present
                    if "velocity=" not in line:
                        line = re.sub(r"(<limit)(.*?>)", r'\1 velocity="1.0"\2', line)

                    modified_lines.append(line)
                else:
                    modified_lines.append(line)

        # Write the modified lines to a new file
        new_file_path = file_path.replace(".xml", "_modified.xml")
        with open(new_file_path, "w") as file:
            file.writelines(modified_lines)
        print(f"Modified file saved as {new_file_path}")

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--data_dir", type=str, default="test_data")
    argparser.add_argument("--data_name", type=str, default="")
    args = argparser.parse_args()
    folder_path = args.data_dir

    if args.data_name:
        modify_urdf(f"{folder_path}/{args.data_name}/mobility.urdf")
    else:
        for data_name in os.listdir(folder_path):
            print(f"Current process: {data_name}")
            if os.path.isdir(os.path.join(folder_path, data_name)):
                modify_urdf(f"{folder_path}/{data_name}/mobility.urdf")
