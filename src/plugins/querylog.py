# sbncng - an object-oriented framework for IRC
# Copyright (C) 2011 Gunnar Beutner
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

from datetime import datetime
from sbnc.plugin import Plugin, ServiceRegistry
from sbnc.proxy import Proxy
from plugins.ui import UIPlugin, UIAccessCheck

proxy_svc = ServiceRegistry.get(Proxy.package)
ui_svc = ServiceRegistry.get(UIPlugin.package)

class QueryLogPlugin(Plugin):
    """Implements query log functionality."""
    
    package = "info.shroudbnc.plugins.querylog"
    name = "querylog"
    description = __doc__

    def __init__(self):
        # register handlers for existing irc connections
        for _, userobj in proxy_svc.users.items():
            for clientobj in userobj.client_connections:
                self._register_handlers(clientobj)
        
        # make sure new irc connections also get the event handlers
        proxy_svc.irc_registration_event.add_handler(self._irc_registration_handler)
        
        proxy_svc.client_registration_event.add_handler(self._client_registration_event)

        ui_svc.register_command('read', self._cmd_read_handler, 'User', 'plays your message log',
                                'Syntax: read\nDisplays your private log.')
        ui_svc.register_command('erase', self._cmd_erase_handler, 'User', 'erases your message log',
                                'Syntax: erase\nErases your private log.')

    def _irc_registration_handler(self, evt, ircobj):
        self._register_handlers(ircobj)
    
    def _client_registration_event(self, evt, clientobj):
        if not 'querylog' in clientobj.owner.tags or len(clientobj.owner.tags['querylog']) == 0:
            return
        
        ui_svc.send_sbnc_reply(clientobj, 'You have new messages. Use \'/msg -sBNC read\' ' +
                               'to view them.', notice=False)
    
    def _register_handlers(self, ircobj):
        ircobj.add_command_handler('PRIVMSG', self._irc_privmsg_handler)
    
    def _irc_privmsg_handler(self, evt, ircobj, nickobj, params):
        if len(params) < 2:
            return
        
        if ircobj.owner == None or len(ircobj.owner.client_connections) > 0:
            return
        
        target = params[0]
        text = params[1]
        
        if ircobj.me.nick != target:
            return
        
        if not 'querylog' in ircobj.owner.tags:
            ircobj.owner.tags['querylog'] = []
        
        item = {
            'timestamp': datetime.now(),
            'source': str(nickobj),
            'text': text
        }
        
        ircobj.owner.tags['querylog'].append(item)
    
    def _cmd_read_handler(self, clientobj, params, notice):
        if not 'querylog' in clientobj.owner.tags or len(clientobj.owner.tags['querylog']) == 0:
            ui_svc.send_sbnc_reply(clientobj, 'Your personal log is empty.', notice)
            return
        
        for message in clientobj.owner.tags['querylog']:
            ui_svc.send_sbnc_reply(clientobj, '[%s] %s: %s' % (message['timestamp'],
                                              message['source'], message['text']), notice)
            
        if notice:
            erasecmd = '/sbnc erase'
        else:
            erasecmd = '/msg -sBNC erase'
            
        ui_svc.send_sbnc_reply(clientobj, 'End of LOG. Use \'%s\' to ' % (erasecmd) +
                               'remove this log.', notice)
    
    def _cmd_erase_handler(self, clientobj, params, notice):
        if not 'querylog' in clientobj.owner.tags or len(clientobj.owner.tags['querylog']) == 0:
            ui_svc.send_sbnc_reply(clientobj, 'Your personal log is empty.', notice)
            return

        clientobj.owner.tags['querylog'] = []
        
        ui_svc.send_sbnc_reply(clientobj, 'Done.', notice)
    
ServiceRegistry.register(QueryLogPlugin)
