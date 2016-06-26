from Crypto.PublicKey import RSA
from base64 import b64decode
import ast

m = "hello world"
key = RSA.generate(1024)
em = key.publickey().encrypt(m.encode('utf-8'),32)[0]

sem = str(em)
print(sem)

msg = key.decrypt(ast.literal_eval(sem))
print(msg)