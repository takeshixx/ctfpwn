import os.path
import aiohttp.web

from ctfpwn.db import CtfDb

db = CtfDb()


def remove_objectid(ilist):
    """Remove MongoDB's _id field
    from query result to make it
    JSON-dumpable."""
    out = list()
    for e in ilist:
        if not '_id' in e.keys():
            continue
        _e = dict(e)
        del _e['_id']
        out.append(_e)
    return out


async def exploits(request):
    exploit_id = request.match_info.get('exploit_id')
    if not exploit_id:
        exploits = await db.select_exploits()
        exploits = remove_objectid(exploits)
        return aiohttp.web.json_response(exploits)


async def create_exploit(request):
    body = await request.post()
    service = body.get('service')
    exploit = body.get('exploit')
    port = body.get('port')
    enabled = body.get('enabled')
    if not service or not exploit or not port or not enabled:
        ret = aiohttp.web.json_response(
            {'error': {'required arguments': ['service', 'exploit', 'port', 'enabled']}})
        ret.set_status(400)
        return ret
    try:
        port = int(port)
    except ValueError:
        ret = aiohttp.web.json_response(
            {'error': {'value error': 'port is not numeric'}})
        ret.set_status(400)
        return ret
    if not enabled in [True, False, 0, 1, 'yes', 'Yes', 'YES', 'no', 'No', 'NO']:
        ret = aiohttp.web.json_response(
            {'error': {'value error': 'invalid value for enabled'}})
        ret.set_status(400)
        return ret
    if not os.path.isfile(exploit):
        ret = aiohttp.web.json_response(
            {'error': {'value error': 'exploit path is invalid'}})
        ret.set_status(400)
        return ret
    result = await db.update_exploit(service, exploit, port, enabled)
    if result['nModified'] > 0:
        return aiohttp.web.Response(status=201, text='Successfully created exploit')
    else:
        return aiohttp.web.Response(status=500, text='Exploit creation failed')


async def modify_exploit(reuqest):
    pass


async def targets(request):
    target_id = request.match_info.get('target_id')
    if not target_id:
        targets = await db.select_alive_targets()
        targets = remove_objectid(targets)
        return aiohttp.web.json_response(targets)


def create_app():
    app = aiohttp.web.Application()
    app.router.add_get('/exploits', exploits)
    app.router.add_post('/exploits', create_exploit)
    app.router.add_get('/exploits/{exploit_id}', exploits)
    app.router.add_put('/exploits/{exploit_id}', modify_exploit)
    app.router.add_get('/targets', targets)
    app.router.add_get('/targets/{targets_id}', targets)
    return app


def run_api():
    app = create_app()
    aiohttp.web.run_app(app, host='127.0.0.1')


if __name__ == '__main__':
    run_api()
