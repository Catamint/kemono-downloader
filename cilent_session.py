import aiohttp

# cilent_session = aiohttp.ClientSession(
#     headers={'Accept': 'text/css'}
# )

def create_session():
    return aiohttp.ClientSession(
    headers={'Accept': 'text/css'}
)