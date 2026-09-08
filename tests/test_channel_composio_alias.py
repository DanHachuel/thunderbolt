from hermes_ui.domain import composio_connected_account_id_from_channel_name


def test_channel_composio_account_id_uses_hyphenated_title_words():
    assert composio_connected_account_id_from_channel_name("The Financial Mechanics") == "The-Financial-Mechanics"
    assert composio_connected_account_id_from_channel_name("Brick by Brick Wealth") == "Brick-by-Brick-Wealth"
    assert composio_connected_account_id_from_channel_name("Canal de Finanças") == "Canal-de-Financas"
