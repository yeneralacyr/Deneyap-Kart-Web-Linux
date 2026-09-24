from utils import executeCli

def searchLibrary(searchTerm:str) -> str:
    """
    for searching libraries using arduino-cli

    :param searchTerm: string that typed to front-end. will be search using arduino-cli
    :type searchTerm: str

    :return: returns string but in json format, will be converted to json on front-end
    :rtype: str
    """

    executeCli(f"lib update-index")
    result = executeCli(f"lib search {searchTerm} --format json")
    return result

def installLibrary(name:str, version:str) -> str:
    """
    :param name: full name of the library
    :type name: str

    :param version: version of the library, like 1.3.12
    :type version: str

    :return: returns subprocess output which is result of arduino-cli execution
    :rtype: str
    """

    result = executeCli(f"lib install \"{name}\"@{version}")
    return result

def installLibraryZip(zipPath:str) -> str:
    """
    That function will take path of .zip file and install library using arduino-cli.
    .zip file will be dropped or selected from front-end, path will be passed this function through Websocket
    """
    raise NotImplemented
    #TODO install from zip
