"""Source slices around the explicit list-attribute lifecycle additions; no synthetic Swift."""
from pathlib import Path
from test_offline_p0_contracts import body

ROOT = Path(__file__).resolve().parents[2]
HOST = 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift'


def segments(test, source, tokens):
    parts = []
    for token in tokens:
        prefix, separator, source = source.partition(token)
        test.assertTrue(separator, token)
        parts.append(prefix)
    return parts + [source]


def pre_attributes_host(test, current):
    from live_item_render_scope_contract import pre_live_render
    current = pre_live_render(current)
    previous = (ROOT / '.local/p0-repair/phase-65/before' / HOST).read_text()
    pairs = {
        'func update(state: ReplicaUIState, cardSide: CGFloat)': (
            ['        if self.state !== state {', '        self.cardSide = cardSide\n'],
            ['        let replacesState = self.state !== state\n        if replacesState {',
             '        self.cardSide = cardSide\n        if replacesState { installListAttributesObservation(state: state) }\n']),
        'func replaceCollectionModel(': (
            ['        items = []\n'], ['        items = []\n        installListAttributesObservation(state: state)\n']),
        'func detachObservers()': (
            ['{\n', '        if let state, state.collectionOwner === self {\n'],
            ['{\n        listAttributesSubscription = nil\n        listAttributesSource = nil\n',
             '        if let state, state.collectionOwner === self {\n            state.listAttributesSource = nil\n'])}
    for marker, (old_tokens, new_tokens) in pairs.items():
        test.assertEqual(segments(test, body(current, marker), new_tokens),
                         segments(test, body(previous, marker), old_tokens))
    for marker in ['private func drainCollectionSnapshots()', 'private func scheduleSnapshotDrain()',
                   'func appliedItems(', 'func update(state: ReplicaUIState, item: ClipboardItem, side: CGFloat, index: Int)']:
        test.assertEqual(body(current, marker), body(previous, marker))
    return previous
