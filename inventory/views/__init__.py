"""
Inventory views package.

Split from the monolithic views.py for better organization.
Each module groups related views by domain.
"""
from .dashboard import *
from .equipment import *
from .maintenance import *
from .handover import *
from .peripheral import *
from .reports import *
from .exports import *
from .pages import *
