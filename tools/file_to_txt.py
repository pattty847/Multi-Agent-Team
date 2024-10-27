def convert_py_to_txt(input_file, output_file):
    try:
        # Open the Python file for reading
        with open(input_file, 'r') as py_file:
            # Read the contents of the file
            file_content = py_file.read()

        # Open the text file for writing
        with open(output_file, 'w') as txt_file:
            # Write the content to the text file
            txt_file.write(file_content)

        print(f"Successfully converted {input_file} to {output_file}")
    
    except FileNotFoundError:
        print(f"The file {input_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
# Replace 'your_file.py' with your Python file and 'output.txt' with your desired text file name
convert_py_to_txt("src/ui/monitor.py", "monitor.txt")
