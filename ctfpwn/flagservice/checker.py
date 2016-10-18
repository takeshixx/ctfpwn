# TODO: this module has never been used, needs proper initial implementation as soon as the rest runs properly.
# from twisted.internet import reactor, defer, protocol, task
#
#
# class CallbackAndDisconnectProtocol(protocol.Protocol):
#     def connectionMade(self):
#         self.factory.deferred.callback(True)
#         self.transport.loseConnection()
#
#
# class ConnectionTestFactory(protocol.ClientFactory):
#     protocol = CallbackAndDisconnectProtocol
#
#     def __init__(self):
#         self.deferred = defer.Deferred()
#
#     def clientConnectionFailed(self, connector, reason):
#         self.deferred.errback(reason)
#
#
# class ServiceChecker(task.LoopingCall):
#
#     def __init__(self, *args, **kwargs):
#         super(ServiceChecker, self).__init__(self.callback, *args, **kwargs)
#         self.db = flag_db
#
#     def callback(self):
#         services = yield self.db.select_services()
#         jobs = [self.check_service(service) for service in services]
#         defer.DeferredList(jobs, consumeErrors=True).addCallback(self.handle_results, services)
#
#     def check_service(self, service):
#         f = ConnectionTestFactory()
#         reactor.connectTCP(service.host, service.port, f)
#         return f.deferred
#
#     def handle_results(self, results, services):
#         for service, result_info in zip(services, results):
#             success, result = result_info
#             if success:
#                 print('Service {} is up'.format(service.name))
#                 self.db.update_service_up(service)
#             else:
#                 print('Service {} is down!'.format(service.name))
#                 self.db.update_service_down(service)
#
#         reactor.stop()
