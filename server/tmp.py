name_list = []
with open('animals.txt','r') as f:
    while True:
	try:
	    tmp_name = f.readline()
	    if len(tmp_name)<=10 and len(tmp_name.split())==1:
		name_list.append(tmp_name)
	except:
	    break

with open('new_animals.txt','w') as f:
    for name in name_list:
	f.write(name+'\n')
