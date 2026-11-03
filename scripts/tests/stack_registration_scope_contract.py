"""Single reviewed registration delta; old frozen contracts retain their original input."""
from pathlib import Path
from stack_native_input_scope_contract import pre_stack_native_inputs

APP_PATH = 'replica/Sources/Pasto/AppMain.swift'
PREVIOUS = ('            && !arguments.contains("--no-global-hotkey") && pasteboard.name == NSPasteboard.general.name\n'
            '            && accessibilityService.f_100ae5e74()\n')
CURRENT = '            && !arguments.contains("--no-global-hotkey") && pasteboard.name == NSPasteboard.general.name\n'

def pre_stack_registration(source):
    source = pre_stack_native_inputs(source)
    if CURRENT in source and PREVIOUS not in source:
        assert source.count(CURRENT) == 1
        return source.replace(CURRENT, PREVIOUS, 1)
    return source
