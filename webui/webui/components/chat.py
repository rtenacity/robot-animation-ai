import reflex as rx
from webui import styles
from webui.components import loading_icon
from webui.state import State, QA

def message(qa: QA) -> rx.Component:
    """A single question/answer message.

    Args:
        qa: The question/answer pair.

    Returns:
        A component displaying the question/answer pair.
    """
    return rx.box(
        rx.box(
            rx.text(
                qa.question,
                bg=styles.border_color,
                shadow=styles.shadow_light,
                **styles.message_style,
            ),
            text_align="right",
            margin_top="1em",
        ),
        rx.box(
            rx.box(
                rx.markdown(
                qa.answer,
                ),
                rx.cond(
                    ~State.video_processing,
                        rx.video(
                            url=State.url,
                            width = "450px",
                            height = "450px",
                                
                                ),

                ),
                bg=styles.accent_color,
                shadow=styles.shadow_light,
                **styles.message_style,
                
            ),
            text_align="left",
            padding_top="1em",
        ),
        width="100%",
    )


def chat() -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.vstack(
        rx.box(rx.foreach(State.chats[State.current_chat], message)),
        py="8",
        flex="1",
        width="100%",
        max_w="3xl",
        padding_x="4",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.box(
        rx.vstack(
            rx.form(
                rx.form_control(
                    rx.hstack(
                        rx.input(
                            placeholder="Type something...",
                            id="question",
                            _placeholder={"color": "#fffa"},
                            _hover={"border_color": styles.accent_color},
                            style=styles.input_style,
                        ),
                        rx.button(
                            rx.cond(
                                State.processing,
                                loading_icon(height="1em"),
                                rx.text("Send"),
                            ),
                            type_="submit",
                            _hover={"bg": styles.accent_color},
                            style=styles.input_style,
                        ),
                    ),
                    is_disabled=State.processing,
                ),
                on_submit=State.process_question,
                reset_on_submit=True,
                width="100%",
            ),
            rx.text(
                "",
                font_size="xs",
                color="#fff6",
                text_align="center",
            ),
            width="100%",
            max_w="3xl",
            mx="auto",
        ),
        position="sticky",
        bottom="0",
        left="0",
        py="4",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {styles.border_color}",
        align_items="stretch",
        width="100%",
    )
    
    
def floating_button():
    return rx.button(
        "Scroll to Bottom",
        on_click=State.scroll_down,
        style={
            "position": "fixed",
            "bottom": "20px",
            "right": "20px"
            
            
        },
        
        bg=styles.accent_color,
        shadow=styles.shadow_light,

    )