# Module 2 -Create a Cryptocurrency 

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  9 17:13:05 2018

@author: magalidrumare
"""

# To be installed 
# Flask ==10.12.2 pip install Flask==0.12.2 
# Flask quick start :http://flask.pocoo.org/docs/0.12/quickstart/#quickstart
# Postman HTTP Client : https://www.getpostman.com/ 
# Requests==2.18.4 pip install requests==2.18.4

# importing the libraries 
import datetime 
import hashlib 
import json
# add request module connecting some nodes in the decentralized blockchain. 
from flask import Flask, jsonify,request
import requests
# to create an url for each node and parse this url. 
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 : Building a Blockchain 
class Blockchain:
    
    def __init__(self):
        self.chain=[]
        # Add a transaction just before creating the block 
        self.transaction=[]
        self.create_block(proof=1, previous_hash='0')
        # No order = not a list but a set 
        self.nodes = set()
        
        
    def create_block (self, proof, previous_hash):
            block={'index':len(self.chain)+1,
                   'timestamp': str(datetime.datetime.now()),
                   'proof': proof,
                   'previous_hash':previous_hash,
                   # When the block function is created, the block created 
                   # Include the transaction list. 
                   'transactions': self.transaction}
            #After the creation of the block we need to make the transaction list empty. 
            self.transaction=[]
            self.chain.append(block)
            return block
        
    def get_previous_block(self): 
        return self.chain[-1]
        
    def proof_of_work(self, previous_proof):
        new_proof=1 
        check_proof=False 
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000': 
                check_proof = True
            else: 
                new_proof +=1
        return new_proof
    
    
    def hash(self, block): 
        encoded_block=json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    
    def is_chain_valid(self,chain): 
        previous_block=chain[0]
        block_index = 1 
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash']!= self.hash(previous_block):
                return False
            previous_proof=previous_block['proof']
            proof=block['proof']
            hash_operation=hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] !='0000': 
                return False 
            previous_block = block 
            block_index +=1
        return True
    
    
    # Create a transaction and append the list of transactions 
    def add_transaction(self,sender,receiver,amount): 
        self.transaction.append({'sender': sender, 
                                  'receiver': receiver,
                                  'amount': amount})
        # Index of the new block that receive the transaction
        previous_block=self.get_previous_block()
        return previous_block['index']+1 
    
    # Add a created node to the set of the node 
    def add_node(self, address): 
        # Parse the url 
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    # Concensus 
    def replace_chain(self): 
        network=self.nodes
        longest_chain= None   
        max_lenght = len(self.chain)
        for node in network: 
            #Request the response of get_chain (lenght)
            response = requests.get(f'http://{node}/get_chain')
            # verification of the validity of the response 
            if response.status_code == 200: 
               # two responses of get_chain: lenght and chain 
               lenght = response.json()['lenght'] 
               chain = response.json()['chain'] 
           # update of the max_lenght
               if lenght>max_lenght and self.is_chain_valid(chain): 
                   max_lenght = lenght
                   longest_chain=chain
        if longest_chain:
            self.chain= longest_chain
            return True 
        return False
    
                     
# Part 2 : Mining the Blockchain 
# Creating a Web App 
app= Flask(__name__)

# Creating an adress for the node on Port 5000
node_address = str(uuid4()).replace('-','')

# Creating a Blockchain 
blockchain=Blockchain()

# Mining the new block 
@app.route('/mine_block', methods=['GET'])
def mine_block(): 
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof= blockchain.proof_of_work(previous_proof)
    previous_hash= blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address, receiver='Hadelin', amount=1)
    block=blockchain.create_block(proof, previous_hash)
    response={'message':'Congratulations, you just mined a block', 
              'index': block['index'],
              'timestamp': block['timestamp'],
              'proof': block['proof'], 
              'previous_hash': block['previous_hash'],
              'transactions' : block['transactions']}
    return jsonify(response),200

@app.route('/get_chain', methods=['GET'])
def get_chain():
    response={'chain':blockchain.chain,
              'lenght': len(blockchain.chain)}
    return jsonify(response),200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid : 
        response= {'message': 'All good.The Blockchain is valid'}
    else: 
        response= {'message': 'Houston we have a problem'}
    return jsonify(response),200   

# Adding a new transaction to the Blockchain 
@app.route('/add_transaction', methods=['POST'])  
def add_transaction(): 
    json = request.get_json()
    transaction_keys= ['sender', 'receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    # Use the add_transaction of the blockchain
    # Arguments are value of the request json['sender'],json['receiver'],json['amount']
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])  
    response = {'message':f'This Transaction will be added to the block{index}'}
    return jsonify(response),201  


# Part 3 : Decentralizing our blockchain 

# Connecting new nodes 
@app.route('/connect_node', methods=['POST']) 
def connect_node(): 
    json = request.get_json()
    nodes= json.get('nodes')
    if nodes is None: 
        return 'No node', 400
    for node in nodes : 
        blockchain.add_node(node)
    response= {'message':'All the nodes are now connected.The Magcoin Blockchain now contains the following nodes:',
        'total_nodes': list(blockchain.nodes)}
    return jsonify(response),201  

#Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced :
        response= {'message': 'The node had different chains to the chain was replaced by the longest one',
                   'new_chain': blockchain.chain}
    else: 
        response= {'message': 'All good.The chain is the largest one',
                   'new_chain': blockchain.chain}
    
    return jsonify(response),200  
   
#Running the app 
    app.run(host='0.0.0.0', port=5001) 