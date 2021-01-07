'''
Tokenizes content of each link
'''
import nltk
from bs4 import BeautifulSoup
from urllib import request
import re

def extract_content(url):
    raw = BeautifulSoup(url,'html.parser')
    for script in raw(["script", "style"]):
        script.extract()
    text = raw.get_text()
    return text
    
def tokenize(content):
    tokens = nltk.word_tokenize(content)
    return tokens

def filter_alphanum(tokens_list):
    temp_tokens = []
    for token in tokens_list:
        if re.match("[a-zA-Z0-9]+",token): #Revisit for 's 
            temp_tokens.append(token.lower())
    return temp_tokens
         
def main():
    url = input()
    html = request.urlopen(url).read().decode('utf8')
    raw_text = extract_content(html)
    tokens_list = tokenize(raw_text)
    alnum_tokens_list = filter_alphanum(tokens_list)
    print(alnum_tokens_list)
    
if __name__ == '__main__':
    main()