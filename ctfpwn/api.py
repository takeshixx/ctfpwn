import asyncio
import os.path
import aiohttp.web
import jinja2
import bson

from ctfpwn.db import CtfDb
from ctfpwn.shared import Service

dashboard_html = """<html>
<head>
    <title>CTF-PWN Dashboard</title>
</head>
<body>
    <h2>Services</h2>
    <table>
        <tr><th>Name</th><th>Type</th><th>Port</th><th>URL</th><th>Meta</th></tr>
        {% for service in services %}
        <tr><td>{{ service.name }}</td><td>{{ service.type }}</td><td>{{ service.port }}</td><td>{{ service.url }}</td><td>{{ service.meta }}</td></tr>
        {% endfor %}
    </table>
    <h2>Create New Service</h2>
    <form action="/api/services" method="post">
        <label for="name">Name</label>
        <input name="name" />
        <label for="type">Type</label>
        <input name="type" />
        <label for="port">Port</label>
        <input name="port" />
        <label for="url">URL</label>
        <input name="url" />
        <label for="meta">Meta</label>
        <input name="meta" />
        <input type="submit" />
    </form>

    <h2>Exploits</h2>
    <table>
        <tr><th>Service</th><th>Exploit</th><th>Port</th><th>Enabled</th></tr>
        {% for exploit in exploits %}
        <tr><td>{{ exploit.service }}</td><td>{{ exploit.exploit }}</td><td>{{ exploit.port }}</td><td>{{ exploit.enabled }}</td></tr>
        {% endfor %}
    </table>
    <h2>Create New Exploit</h2>
    <form action="/api/exploits" method="post">
        <label for="service">Service</label>
        <input name="service" />
        <label for="exploit">Exploit</label>
        <input name="exploit" type="file" />
        <label for="port">Port</label>
        <input name="port" />
        <label for="enabled">Enabled</label>
        <input name="enabled" type="checkbox" />
        <input type="submit" />
    </form>
</body>
</html>"""


def cast_objectid(ilist):
    """Cast MongoDB's ObjectID to a string
    to make the API dict's JSON-dumpable."""
    out = list()
    for e in ilist:
        if not '_id' in e.keys():
            continue
        _e = dict(e)
        _e['_id'] = str(bson.ObjectId(_e['_id']))
        out.append(_e)
    return out


async def dashboard(request):
    services = await db.select_all_services()
    exploits = await db.select_exploits()
    ret = jinja2.Environment().from_string(dashboard_html).render(services=services,
                                                                  exploits=exploits)
    return aiohttp.web.Response(text=ret, content_type='text/html')


async def index(request):
    return aiohttp.web.json_response({'endpoints': ['/exploits',
                                                    '/targets',
                                                    '/services']})

async def exploits(request):
    exploit_id = request.match_info.get('exploit_id')
    if not exploit_id:
        exploits = await db.select_exploits()
        exploits = cast_objectid(exploits)
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
    if str(enabled).lower() in ['true', 'yes', '1']:
        enabled = True
    elif str(enabled).lower() in ['false', 'no', '0']:
        enabled = False
    else:
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
    if result['nModified'] > 0 or result['ok'] > 0:
        return aiohttp.web.Response(status=201, text='Successfully created exploit')
    else:
        return aiohttp.web.Response(status=500, text='Exploit creation failed')


async def delete_exploit(request):
    exploit_id = request.match_info.get('exploit_id')
    if exploit_id:
        result = await db.delete_exploit(exploit_id)
        if result and result.get('ok') > 0:
            if result.get('n') > 0:
                return aiohttp.web.Response(status=200, text='Successfully deleted exploit')
            else:
                return aiohttp.web.Response(status=404, text='Exploit not found')
        else:
            return aiohttp.web.Response(status=500, text='Exploit deletion failed')


async def targets(request):
    target_id = request.match_info.get('target_id')
    if not target_id:
        targets = await db.select_alive_targets()
        targets = cast_objectid(targets)
        return aiohttp.web.json_response(targets)


async def services(request):
    service_id = request.match_info.get('service_id')
    if not service_id:
        services = await db.select_all_services()
        services = cast_objectid(services)
        return aiohttp.web.json_response(services)


async def create_service(request):
    body = await request.post()
    name = body.get('name')
    service_type = body.get('type')
    port = body.get('port')
    url = body.get('url')
    meta = body.get('meta')
    if not name or not service_type or not (port or url):
        ret = aiohttp.web.json_response(
            {'error': {'required arguments': ['name', 'service_type', 'port', 'url']}})
        ret.set_status(400)
        return ret
    if type == 'port' and (port and url):
        ret = aiohttp.web.json_response(
            {'error': {'invalid argument': 'either port or url should be defined (not both)'}})
        ret.set_status(400)
        return ret
    if port:
        try:
            port = int(port)
        except ValueError:
            ret = aiohttp.web.json_response(
                {'error': {'value error': 'port is not numeric'}})
            ret.set_status(400)
            return ret
    if not service_type in ['port', 'url']:
        ret = aiohttp.web.json_response(
            {'error': {'invalid type': 'type should be port or url'}})
        ret.set_status(400)
        return ret
    if service_type == 'port':
        service = Service(name, service_type, port=port, meta=meta)
    else:
        service = Service(name, 'url', url=url, port=port, meta=meta)
    result = await db.insert_service(service)
    if result['nModified'] > 0 or result['ok'] > 0:
        return aiohttp.web.Response(status=200, text='Successfully created service')
    else:
        return aiohttp.web.Response(status=500, text='Service creation failed')


async def delete_service(request):
    service_id = request.match_info.get('service_id')
    if service_id:
        result = await db.delete_service(service_id)
        if result and result.get('ok') > 0:
            if result.get('n') > 0:
                return aiohttp.web.Response(status=200, text='Successfully deleted service')
            else:
                return aiohttp.web.Response(status=404, text='Service not found')
        else:
            return aiohttp.web.Response(status=500, text='Service deletion failed')


def create_app():
    app = aiohttp.web.Application()
    app.router.add_get('/', dashboard)
    app.router.add_get('/api', index)
    app.router.add_get('/api/exploits', exploits)
    app.router.add_post('/api/exploits', create_exploit)
    app.router.add_get('/api/exploits/{exploit_id}', exploits)
    app.router.add_delete('/api/exploits/{exploit_id}', delete_exploit)
    app.router.add_get('/api/targets', targets)
    app.router.add_get('/api/targets/{targets_id}', targets)
    app.router.add_get('/api/services', services)
    app.router.add_post('/api/services', create_service)
    app.router.add_get('/api/services/{service_id}', services)
    app.router.add_delete('/api/services/{service_id}', delete_service)
    return app


async def database():
    global db
    db = await CtfDb.create()


def run_api(config=None):
    if config:
        host = config['api_listening_host']
        port = config['api_listening_port']
    else:
        host = '127.0.0.1'
        port = 8080
    loop = asyncio.get_event_loop()
    loop.create_task(database())
    app = create_app()
    aiohttp.web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    run_api()
