import aiohttp
from aiohttp_socks import ProxyConnector

class SessionManager:

    _global_proxy = None

    def __init__(self):
        self._sessions = []

    @classmethod
    def set_global_proxy(cls, proxy_url: str | None):
        """设置全局代理，None 表示不用代理"""
        cls._global_proxy = proxy_url

    def get_connector(self, connector: aiohttp.BaseConnector | None = None) -> aiohttp.BaseConnector | None:
        """返回可用的 connector，如果传入则用传入的，否则用全局代理"""
        if connector is not None:
            return connector
        if self._global_proxy:
            return ProxyConnector.from_url(self._global_proxy)
        return None
    
    def create_session(
        self,
        headers: dict | None = None,
        connector: aiohttp.BaseConnector | None = None,
    ) -> aiohttp.ClientSession:
        """创建一个新session，带有 headers / connector"""
        conn = self.get_connector(connector)
        session = aiohttp.ClientSession(
            trust_env=True, 
            headers=headers, 
            connector=conn
        )
        self._sessions.append(session)
        return session
    
    async def close_all(self):
        """关闭所有session"""
        for s in self._sessions:
            if not s.closed:
                await s.close()
        self._sessions.clear()

session_manager = SessionManager()