import jwt
from jwt.exceptions import ExpiredSignatureError
import datetime
import json
import time

expiration = 5

token = jwt.encode(
            {'id': 1,
             'exp': datetime.datetime.now().timestamp() + datetime.timedelta(seconds=expiration).seconds
             },
            'cfd36353845324a3d7fee472955de516cfd36353845324a3d7fee472955de516',
            algorithm="HS256"
)

print(token)
time.sleep(10)
try:
    print(jwt.decode(token, 'cfd36353845324a3d7fee472955de516cfd36353845324a3d7fee472955de516', algorithms=["HS256"]))
except ExpiredSignatureError as error:
    print(error)
