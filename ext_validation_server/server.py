from logging import log
from flask import Flask, request
import json
from loguru import logger
logger.add('byoctf_ext_server.log')

app = Flask(__name__)

@app.route('/validate', methods=['GET', 'POST'])
def validate():
    if request.method != 'POST':
        logger.debug("get request")
        return {
            'status':'ok', 
            'msg':'you must post to this endpoint ex: {"id":1, "flag":"FLAG{ABC}", "user": "someuser#1234"}'
        }
    
    if request.form == None:
        logger.debug('malformed request')
        return {'msg':'malformed request'}, 400

    flags = {}
    with open('flags.json') as f:
        try:
            flags = json.loads(f.read())
        except BaseException as e:
            logger.debug(f'failed to load flags.json:{e}')
            return {'msg': f'{e}'}

    chall_id    = request.form.get('challenge_id')
    flag        = request.form.get('flag')
    user        = request.form.get('user')


    logger.debug(f"Attempt from {user} for chall {chall_id} with {flag}")

    if flag == flags.get(chall_id): #
        logger.debug("correct")
        return {'msg':'correct'}    

    logger.debug("incorrect")
    return {'msg':'incorrect'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)