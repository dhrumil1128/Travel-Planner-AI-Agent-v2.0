# Legal Entity Extractor - Proof of Concept  
from transformers import pipeline  

# Load specialized legal NLP model  
legal_ner = pipeline("ner", model="dslim/bert-base-NER")  

# Sample Supreme Court text  
text = 
'''Chief Justice Roberts delivered the opinion in Brown v. Board of Education,  
a landmark 1954 case that declared school segregation unconstitutional.'''
# Extract entities  
results = legal_ner(text)  

# Pretty print results  
for entity in results:  
    print(f"{entity['word']} → {entity['entity']}")  
