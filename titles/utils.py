import re 

class ReList(list):
    """
    A list that stores regexps.

    You can add compiled or uncompiled regexps to the list.
    It will always return the compiled version.
    It will compile the text regexps on demand when first accessed.
    """

# Set the default flags
    flags = re.IGNORECASE | re.UNICODE

    def __init__(self, *args, **kwargs):
        """Optional :flags: keyword argument with regexp flags to compile with"""
        if 'flags' in kwargs:
            self.flags = kwargs['flags']
            del kwargs['flags']
        list.__init__(self, *args, **kwargs)

    def __getitem__(self, k):
        item = list.__getitem__(self, k)
        if isinstance(item, basestring):
            item = re.compile(item, re.IGNORECASE | re.UNICODE)
            self[k] = item
        return item

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


