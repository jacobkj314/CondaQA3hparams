'''
    This script takes the json from a CONDAQA dataset partition and groups it by ORIGINAL PASSAGE, then QUESTION, then EDIT
    The output is a list of( (each original passage's) list of( question and list of (edited passages and editID and label)) )
'''

import re, json
from sys import argv

def sortByQuestion(gathered):
	questions = set(d["question"] for d in gathered)
	return [
			{
				"question":q, 
				"contexts":[
							{
								"passage":e["passage"], 
								"editID":e["editID"], 
								"label":e["label"]
							} 
	 						for e in gathered 
							if e["question"] == q
						   ]
			} 
	 			for q in questions
		   ]


def json2data(url, sortBy=sortByQuestion):
	with open(url, "r") as file:
		text = file.read()
	jsonArray = "[" + re.sub("\n", ",", text[:-1]) + "]" #format as json array
	jsonData = json.loads(jsonArray)
	
	passageIDs = set(d["PassageID"] for d in jsonData)
	
	def gather(pId):
		return [
					{
						"editID":d["PassageEditID"], 
						"passage":d['sentence1'], 
						"question":d['sentence2'], 
						"label":d['label']
					} 
					for d in jsonData 
					if d["PassageID"] == pId
			   ]
	
	return [sortBy(gather(i)) for i in passageIDs]

def json2bundles(url):
	data = json2data(url)
	bundles = []

	for passage in data:
		curr_bundles = []
		for bundle in passage:
			curr_bundles.append(
				{
					"input": [(bundle['question'] + '\n' + context['passage']) for context in bundle['contexts']],
					"answer": [(context['label']) for context in bundle['contexts']]
				}
			)

		if '-mq' in argv: #multi-question
			None # merge the bundles together
			complete_input = []; complete_answer = []
			for b in curr_bundles:
				complete_input.extend(b['input']); complete_answer.extend(b['answer'])
			curr_bundles = [{"input":complete_input, "answer":complete_answer}]
		if '-fa' in argv: #filter-answers
			filtered_bundles = []
			for bun in curr_bundles:
				bun_in = bun['input']; bun_ans = bun['answer']
				filt_in = []; filt_ans = []
				ansset = set()
				for que, ans in zip(bun_in, bun_ans):
					if ans not in ansset:
						ansset.add(ans)
						filt_in.append(que)
						filt_ans.append(ans)
				filtered_bundles.append({"input":filt_in, "answer":filt_ans})
			curr_bundles = filtered_bundles
		
		bundles.extend(curr_bundles)

	return bundles

def bundle(source, destination):
	bundles = json2bundles(source)

	with open(destination, "w") as out:
		out.write('')
	with open(destination, "a") as out:
		for bundle in bundles:
			out.write(json.dumps(bundle) + '\n')

bundle("data/condaqa_train.json", "data/unifiedqa_formatted_data/condaqa_train_unifiedqa.json")
