import sys
import xml.etree.ElementTree as ET
import json
import base64


def verify_size_file():
	# return at the begining of the file
	file_binary.seek(0,0)
	# Verify size of OpenedFile against the size value on the structure child in the XML file
	file_binary.seek(0,2)
	size_file_binary = str(file_binary.tell())

	size_file_on_xml = ''
	for child in root:
		if child.tag == 'structure' and child.attrib['file'] == extension_value:
			size_file_on_xml = child.find('check').find('size').text

	if size_file_on_xml != size_file_binary:
		return False
	return True


def build_structure():
	# return at the begining of the file
	file_binary.seek(0, 0)
	for child in root:
		if child.tag == 'structure' and child.attrib['file'] == extension_value:
			for structure_child in child:
				if structure_child.tag == 'elt':
					datas = structure_child.attrib
					datas['etl_value_in_bytes'] = base64.standard_b64encode(file_binary.read(int(structure_child.attrib['size'])))
					data_structure.append(datas)
				if structure_child.tag == 'loop':
					range_start = 0
					if 'start' in structure_child.attrib:
						range_start = int(structure_child.attrib['start'])
					range_end = int(structure_child.attrib['count'])
					for x in range(range_start, range_end):
						datas = {}
						datas['LOOP'] = 'LOOP_' + structure_child[0].attrib['id']
						datas['INC'] = str(x)
						for loop_child in structure_child:
							datas_loop = []
							if loop_child.tag == 'elt':
								datas_loop_value = {}
								for key in loop_child.attrib:
									datas_loop_value[key] = loop_child.attrib[key]
								datas_loop_value['etl_value_in_bytes'] = base64.standard_b64encode(file_binary.read(int(loop_child.attrib['size'])))
								datas_loop.append(datas_loop_value)
								datas['VALUES_' + loop_child.attrib['id'] + '_' + str(x) ] = datas_loop
						data_structure_loop.append(datas)


def convert_value_from_bytes(output_id):
	final_value = ''
	json_parser = json.loads(output_id.replace('\'', '\"').replace('b"', '"'))
	value = base64.standard_b64decode(json_parser['etl_value_in_bytes'].replace('\'', '\"'))

	if 'int' in json_parser['type']:
		if '16' in json_parser['base']:
			if 'endianness' in json_parser:
				if 'little_endian' in json_parser['endianness']:
					final_value = int(value[::-1].hex())
			if 'nibble-skip' in json_parser:
				if 'odd' in json_parser['nibble-skip']:
					# 01AB01CD -> nibble-skip="odd" -> 1B1D (in base 16)
					working_value = ''
					value = value.hex()
					for x in range(1,len(value),2):
						working_value = working_value + value[x]
					final_value = int(working_value)
			if final_value == '':
				final_value = int(value.hex())
		return final_value

	elif 'raw' in json_parser['type']:
		return value.hex()

	elif 'text' in json_parser['type']:
		# Replace Robotron 0x3A by " " => 0x3A = :
		#<charset id="robotron">
		#	<char src="0x3A" dst=" "/>
		#  </charset>
		if 'nibble-skip' in json_parser:
			if 'odd' in json_parser['nibble-skip']:
				final_value = ''
				value = value.hex()
				for x in range(1,len(value),2):
					final_value = final_value + value[x]
				return bytearray.fromhex(final_value).decode()
		else:
			value = value.hex()
			return bytearray.fromhex(value).decode()


def format_converted_value(value_to_format, format_value):

	final_value = 'VALUE_TO_FORMAT'
	for child2 in root:
		if child2.tag == 'format':
			if format_value in child2.attrib['id']:
				working_value = value_to_format
				for subchild in child2:
					if 'case' in subchild.tag:
						if int(subchild.attrib['src']) == int(working_value):
							final_value = subchild.attrib['dst']
					elif 'multiply' in subchild.tag:
						final_value = str(int(working_value) * int(subchild.text))
					elif 'add' in subchild.tag:
						final_value = str(int(working_value) + int(subchild.text))
	return final_value


def print_fields():

	for child in root:
		if child.tag == 'output':
			for output_child in child:
				format_value = ''
				if output_child.tag == 'field':
					if 'format' in output_child.attrib:
						format_value = output_child.attrib['format']
					for x in  data_structure:
						if output_child.attrib['id'] in str(x):
							datas_child_field = []
							datas_child_field.append(output_child.attrib['id'])
							working_value = ''
							working_value = convert_value_from_bytes(str(x))
							if format_value != '':
								working_value = format_converted_value(working_value, format_value)
							datas_child_field.append(working_value)
					if len(datas_child_field) > 0:
						print(datas_child_field)


def print_table_fields():
	
	for child in root:
		if child.tag == 'output':
			for output_child in child:
				format_value = ''
				if output_child.tag == 'table':
					title_child_table = []
					datas_child_table_field = []
					for table_child in output_child:
						if 'format' in output_child.attrib:
							format_value = output_child.attrib['format']
						if table_child.tag == 'field':
							title_child_table.append(table_child.attrib['id'])
							for x in  data_structure:
								if table_child.attrib['id'] in str(x):
									working_value = ''
									working_value = convert_value_from_bytes(str(x))
									if format_value != '':
										working_value = format_converted_value(working_value, format_value)
									datas_child_table_field.append(working_value)
							
					if len(title_child_table) > 0:
						print(title_child_table)
					if len(datas_child_table_field) > 0:
						print(datas_child_table_field)


def print_table_columns():

	for child in root:
		if child.tag == 'output':
			for output_child in child:
				format_value = ''
				if output_child.tag == 'table':
					title_child_table = []
					datas_child_table_column = []
					for table_child in output_child:
						if 'format' in output_child.attrib:
							format_value = output_child.attrib['format']
						if table_child.tag == 'column':
							title_child_table.append(table_child.attrib['id'])
							for datas_values in data_structure_loop:
								if 'LOOP_' + table_child.attrib['id']  in str(datas_values):
									datas_child_table_column.append(datas_values)

					datas_child_table_column_print = []
					for values_column_datas in datas_child_table_column:
						datas = []
						for title_column in title_child_table:
							if title_column == 'RANK':
								# continue
								datas.append(int(values_column_datas['INC']) + 1)
							else:
								for key_column in values_column_datas:
									if key_column == 'VALUES_' + title_column + '_' + values_column_datas['INC']:
										working_value = ''
										working_value = convert_value_from_bytes(str(values_column_datas[key_column][0]))
										if format_value != '':
											working_value = format_converted_value(working_value, format_value)
										datas.append(working_value)
						datas_child_table_column_print.append(datas)
					
					if len(title_child_table) > 0:
						print(title_child_table)
					for toto in datas_child_table_column_print:
						print(toto)


# Start Program
# example : python hi2txt.py robotron.xml robotron.nvram

# GetExtension of sys.argv[1] and sys.argv[2]
if not sys.argv[1].endswith('.xml'):
	print('ERR : not xml file')
	exit()

if sys.argv[2].endswith('.nvram'):
	extension_value = 'nvram'
elif sys.argv[2].endswith('.hi'):
	extension_value = '.hi'
else:
	print('ERR : not supported files')
	exit()

# Parse XML File of hitext
tree = ET.parse(sys.argv[1])
root = tree.getroot()
# OpenFile (*.hi or *.nvram)
file_binary = open(sys.argv[2], "rb")

if not verify_size_file():
	print('Size Not OK')
	exit()

# List structure of datas from nvram file or hi file following informations of xml file
data_structure = []
data_structure_loop = []
# Build structure
build_structure()
# Print in the console
print_fields()
print_table_fields()
print_table_columns()
# print(data_structure_loop)
