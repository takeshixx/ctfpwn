import asyncio
import os.path
import aiohttp.web
import jinja2
import bson
import bson.json_util
import subprocess

from ctfpwn.db import CtfDb
from ctfpwn.shared import Service, load_ctf_config
from ctfpwn.exploitservice.worker import ExploitWorkerProtocol

dashboard_html = """<html>
<head>
    <title>CTF-PWN Dashboard</title>
</head>
<body>
    <h2>Services</h2>
    <table border="1" cellpadding="5" cellspacing="5">
        <tr><th>Name</th><th>Type</th><th>Port</th><th>URL</th><th>Meta</th></tr>
        {% for service in services %}
        <tr><td>{{ service.name }}</td><td>{{ service.type }}</td><td>{{ service.port }}</td><td>{{ service.url }}</td><td>{{ service.meta }}</td><td><a href="/api/services/{{ service._id }}/delete">delete</a></td></tr>
        {% endfor %}
    </table>
    <h2>Create New Service</h2>
    {% if service_create_error %}
        <span style="border: 3px solid red">{{ service_create_error }}</span>
    {% endif %}
    {% if service_message %}
        <span style="border: 3px solid green">{{ service_message }}</span>
    {% endif %}
    <table>
        <form action="/api/services" method="post">
        <tr>
            <td><label for="name">Name</label></td>
            <td><input name="name" /></td>
        </tr>
        <tr>
            <td><label for="type">Type</label></td>
            <td><input name="type" /></td>
        </tr>
        <tr>
            <td><label for="port">Port</label></td>
            <td><input name="port" /></td>
        </tr>
        <tr>
            <td><label for="url">URL</label></td>
            <td><input name="url" /></td>
        </tr>
        <tr>
            <td><label for="meta">Meta</label></td>
            <td><input name="meta" /></td>
        </tr>
        <tr>
            <td><input type="submit" /></td>
        </tr>
        </form>
    </table>
    <hr />
    <h2>Exploits</h2>
    <table border="1" cellpadding="5" cellspacing="5">
        <tr><th>Service</th><th>Exploit</th><th>Port</th><th>Enabled</th></tr>
        {% for exploit in exploits %}
        <tr><td>{{ exploit.service }}</td><td>{{ exploit.exploit }}</td><td>{{ exploit.port }}</td><td>{{ exploit.enabled }}</td><td><a href="/api/exploits/{{ exploit._id }}/enable">enable</a></td><td><a href="/api/exploits/{{ exploit._id }}/disable">disable</a></td><td><a href="/api/exploits/{{ exploit._id }}/delete">delete</a></td><td><a href="/api/exploits/{{ exploit._id }}/check">check</a></td></tr>
        {% endfor %}
    </table>
    <h2>Create New Exploit</h2>
    {% if exploit_create_error %}
        <span style="border: 3px solid red">{{ exploit_create_error }}</span>
    {% endif %}
    {% if exploit_message %}
        <span style="border: 3px solid green">{{ exploit_message }}</span>
    {% endif %}
    <table>
        <form action="/api/exploits" method="post">
        <tr>
            <td><label for="service">Service</label></td>
            <td><input name="service" /></td>
        </tr>
        <tr>
            <td><label for="exploit">Exploit</label></td>
            <td><input name="exploit" /></td>
        </tr>
        <tr>
            <td><label for="port">Port</label></td>
            <td><input name="port" /></td>
        </tr>
        <tr>
            <td><input type="submit" /></td>
        </tr>
        </form>
    </table>
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
        return aiohttp.web.json_response(exploits, dumps=bson.json_util.dumps)


async def create_exploit(request):
    body = await request.post()
    service = body.get('service')
    exploit = body.get('exploit')
    port = body.get('port')
    enabled = body.get('enabled')
    if not service or not exploit or not port:
        ret = aiohttp.web.json_response(
            {'error': {'required arguments': ['service', 'exploit', 'port']}})
        ret.set_status(400)
        return ret
    try:
        port = int(port)
    except ValueError:
        ret = aiohttp.web.json_response(
            {'error': {'value error': 'port is not numeric'}})
        ret.set_status(400)
        return ret
    if str(enabled).lower() in ['true', 'yes', 'on', '1']:
        enabled = True
    elif str(enabled).lower() in ['false', 'no', 'off', '0'] or enabled == None:
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


async def modify_exploit(request):
    exploit_id = request.match_info.get('exploit_id')
    if not exploit_id:
        return aiohttp.web.Response(status=400, text='Exploit ID not set')
    exploit_action = request.match_info.get('exploit_action')
    if not exploit_action:
        return aiohttp.web.Response(status=400, text='Exploit action not set')
    exploit = await db.select_exploit_id(exploit_id)
    if not exploit:
        return aiohttp.web.Response(status=404, text='Exploit not found')
    exploit = exploit[0]
    if exploit_action == 'enable':
        await db.toggle_exploit(exploit_id, True)
        return aiohttp.web.HTTPFound('/')
    elif exploit_action == 'disable':
        await db.toggle_exploit(exploit_id, False)
        return aiohttp.web.HTTPFound('/')
    elif exploit_action == 'delete':
        result = await db.delete_exploit_id(exploit_id)
        if result and result.get('ok') > 0:
            if result.get('n') > 0:
                return aiohttp.web.Response(status=200, text='Successfully deleted exploit')
            else:
                return aiohttp.web.Response(status=404, text='Exploit not found')
        else:
            return aiohttp.web.Response(status=500, text='Exploit deletion failed')
    elif exploit_action == 'check':
        if not os.access(exploit.get('exploit'), os.F_OK):
            return aiohttp.web.Response(status=500, text='Cannot access exploit file!')
        if not os.access(exploit.get('exploit'), os.R_OK):
            return aiohttp.web.Response(status=500, text='Cannot read exploit file!')
        if not os.access(exploit.get('exploit'), os.X_OK):
            return aiohttp.web.Response(status=500, text='Exploit is not executable!')
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        cmd = [exploit.get('exploit'), '1.2.3.4', '12345']
        protocol_factory = lambda: ExploitWorkerProtocol(future, cmd)
        transport, protocol = await loop.subprocess_exec(protocol_factory, *cmd, stdin=None)
        try:
            await future
        except subprocess.CalledProcessError as e:
            ret = 'Exploit execution failed with exception:\n\n' + str(e)
            process_output = bytes(protocol.output)
            if process_output:
                ret += '\n\n\n\nProcess output:\n\n' + process_output.decode()
            return aiohttp.web.Response(status=500, text=ret)
        return aiohttp.web.Response(status=200, text='Everything is fine, ride on :)')
    else:
        return aiohttp.web.Response(status=400, text='Invalid exploit action')


async def targets(request):
    target_id = request.match_info.get('target_id')
    if not target_id:
        targets = await db.select_alive_targets()
        targets = cast_objectid(targets)
        return aiohttp.web.json_response(targets, dumps=bson.json_util.dumps)


async def services(request):
    service_id = request.match_info.get('service_id')
    if not service_id:
        services = await db.select_all_services()
        services = cast_objectid(services)
        return aiohttp.web.json_response(services, dumps=bson.json_util.dumps)


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
        return aiohttp.web.Response(status=201, text='Successfully created service')
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


async def modify_service(request):
    service_id = request.match_info.get('service_id')
    if not service_id:
        return aiohttp.web.Response(status=400, text='Service ID not set')
    service_action = request.match_info.get('service_action')
    if not service_action:
        return aiohttp.web.Response(status=400, text='Service action not set')
    if service_action == 'delete':
        result = await db.delete_service_id(service_id)
        if result and result.get('ok') > 0:
            if result.get('n') > 0:
                return aiohttp.web.Response(status=200, text='Successfully deleted service')
            else:
                return aiohttp.web.Response(status=404, text='Service not found')
        else:
            return aiohttp.web.Response(status=500, text='Service deletion failed')
    else:
        return aiohttp.web.Response(status=400, text='Invalid service action')


def create_app():
    app = aiohttp.web.Application()
    app.router.add_get('/', dashboard)
    app.router.add_get('/api', index)
    app.router.add_get('/api/exploits', exploits)
    app.router.add_post('/api/exploits', create_exploit)
    app.router.add_get('/api/exploits/{exploit_id}', exploits)
    app.router.add_get('/api/exploits/{exploit_id}/{exploit_action}', modify_exploit)
    app.router.add_delete('/api/exploits/{exploit_id}', delete_exploit)
    app.router.add_get('/api/targets', targets)
    app.router.add_get('/api/targets/{targets_id}', targets)
    app.router.add_get('/api/services', services)
    app.router.add_post('/api/services', create_service)
    app.router.add_get('/api/services/{service_id}', services)
    app.router.add_get('/api/services/{service_id}/{service_action}', modify_service)
    app.router.add_delete('/api/services/{service_id}', delete_service)
    return app


async def database():
    global db
    db = await CtfDb.create()


def run_api(config=None):
    if config:
        config = load_ctf_config(config)
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
