class TradeValidator:

    def __init__(self, number_of_shares_to_trade: int):
        self.number_of_shares_to_trade = number_of_shares_to_trade

    def validate_ask(self, available_shares_to_sell:int) -> (str, str):
        if self.number_of_shares_to_trade > available_shares_to_sell:
            return 'quantity', 'That many shares are not available.'

        return None, None

    def validate_bid(self, bid_price:int, incentives_available:int,
            total_shares:int) -> (str, str):

        if self.number_of_shares_to_trade > total_shares:
            return 'quantity', 'That project does not have that many shares.'

        if bid_price * self.number_of_shares_to_trade > incentives_available:
            return ('price',
                    'You do not have that many reputation points available.')

        return None, None
