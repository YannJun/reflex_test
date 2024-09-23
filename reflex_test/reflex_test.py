import functools
import reflex as rx
import time
from rxconfig import config
import random
import string
import datetime

TTL = 4 * 60


class State(rx.State):
    access_token: str = rx.SessionStorage(name='access-token')
    expire_at: int = rx.SessionStorage(name='expire_at')
    cookie: str = rx.Cookie(name='cookie')

    # @rx.var
    # def token_is_valid(self) -> bool:
    #     try:
    #         # self.set_cookie('qsdqsdqsd')
    #         print('Token is valid')
    #         return True
    #     except Exception:
    #         return False

    @rx.var
    def protected_data(self):
        data = 'Protected data'
        return data
    
    @rx.var
    def is_token_valid(self) -> bool:
        if self.expire_at:
            print(int(self.expire_at) - round(time.time()))
        if not self.access_token:
            return False
        elif self.expire_at and int(self.expire_at) < round(time.time()):
            return False
        return True
    
    def callback(self):
        print(f'Callback ({self.router.page.path}) being called')
        return rx.redirect('/login?code=123&state=123')

    def login(self, date=None):
        if date:
            print('Triggering token renew at TTL')
            print(int(self.expire_at) - round(time.time()))
        if self.access_token:
            print(f'Current token is {self.access_token}, expiring at {self.expire_at}')
        # print(f'Current url {self.router.page.full_path}')
        print(f'Current url {self.router.page.full_raw_path}')
        # print(f'Current full url {self.router.page.full_raw_path}')
        print(f'Current Params {self.router.page.params}')
        fake_callback_url = r'http://localhost:3000/callback'
        # Get code from callback
        if not self.is_token_valid:
            print('Token is not valid')
            if (
                not self.router.page.params
            ):
                print('Redirecting to login')
                return rx.redirect(fake_callback_url)
            
            if (
                self.router.page.path == '/login'
                and self.router.page.params.get('code')
            ):  
                print('Getting new token')
                print(self.router.page.full_path)
                print(self.router.page.params)
                # new_token = ''.join([str(i)*10 for i in random.choice(string.ascii_uppercase + string.digits)])
                new_token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
                self.set_access_token(new_token)
                expire_at = datetime.datetime.now() + datetime.timedelta(minutes=TTL)
                self.set_expire_at(round(expire_at.timestamp()))

                return rx.redirect(self.router.page.full_path)
    
def require_login(page) -> rx.Component:
    @functools.wraps(page)
    def _auth_wrapper() -> rx.Component:
        return rx.container(
            rx.vstack(
                rx.cond(
                    State.is_hydrated,
                    rx.cond(
                        State.token_is_valid, page(), login()
                    ),
                    rx.spinner(),
                ),
                # client_id=CLIENT_ID,
            )
        )

    return _auth_wrapper

def callback():
    print('Callback being called')
    return rx.redirect('/login?code=123&state=123')

@rx.page(
    route="/login",
    on_load=State.login
)
def login() -> rx.Component:
    return rx.vstack(
        rx.text("Logging in"),
    )

@rx.page(route="/callback", on_load=State.callback)
def callback() -> rx.Component:
    return rx.flex(
        rx.text('Fakse Callback Page, Redirecting')
    )

# @require_login
# @rx.page(route="/protected")
def protected() -> rx.Component:
    # State.set_access_token('my_token')
    # State.set_cookie('my_cookie')
    return rx.container(
        rx.vstack(
            rx.text(State.protected_data),
            rx.button(
                f"Set cookie: '{State.cookie}' '{State.access_token}' '{State.access_token2}'",
                on_click=[
                    State.set_cookie("my_cookie"),
                    State.set_access_token("my_token"),
                    # State.set_access_token2("my_token2")
                ],
            )
        )
    )

# @require_login
# @rx.page(route="/")
def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.flex(
        rx.el.Iframe.create(
            src="/login"
        ),
        rx.text("Welcome to Reflex"),
        rx.color_mode.button(position="top-right"),
        rx.logo(),
        rx.moment(
            interval=TTL*1000,
            on_change=State.login,
            # display="none",
        )
    )

app = rx.App(
    theme=rx.theme(
        appearance="light", has_background=True, radius="large", accent_color="teal"
    )
)
app.add_page(index)
