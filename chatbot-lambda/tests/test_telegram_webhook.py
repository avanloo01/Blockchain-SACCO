from unittest.mock import MagicMock, patch

from src.handlers.telegram_webhook import handle_telegram_update


@patch("src.handlers.telegram_webhook.send_message")
@patch("src.handlers.telegram_webhook.get_member_by_chat_id", return_value=None)
@patch("src.handlers.telegram_webhook.dispatch_command", return_value="Please sign up first")
def test_unlinked_user_gets_contact_keyboard(_mock_dispatch, _mock_member, mock_send) -> None:
    mock_send.return_value = {"ok": True, "result": {"message_id": 42}}

    result = handle_telegram_update(
        {
            "update_id": 1,
            "message": {
                "chat": {"id": 123},
                "text": "/start",
            },
        }
    )

    assert result["ok"] is True
    kwargs = mock_send.call_args.kwargs
    assert kwargs["reply_markup"]["keyboard"][0][0]["request_contact"] is True


@patch("src.handlers.telegram_webhook.send_message")
@patch("src.handlers.telegram_webhook.get_member_by_chat_id")
@patch("src.handlers.telegram_webhook.link_member_by_phone")
def test_contact_message_links_member(mock_link, mock_member, mock_send) -> None:
    linked_member = MagicMock(id="mem-1", phone="+254 700 000000")
    mock_link.return_value = linked_member
    mock_member.return_value = linked_member
    mock_send.return_value = {"ok": True, "result": {"message_id": 99}}

    result = handle_telegram_update(
        {
            "update_id": 2,
            "message": {
                "chat": {"id": 123},
                "contact": {
                    "phone_number": "+254700000000",
                    "user_id": 123,
                },
            },
        }
    )

    assert result["ok"] is True
    mock_link.assert_called_once_with(telegram_chat_id="123", phone="+254700000000")
    kwargs = mock_send.call_args.kwargs
    assert kwargs["reply_markup"] == {"remove_keyboard": True}
    assert "now linked" in kwargs["text"]