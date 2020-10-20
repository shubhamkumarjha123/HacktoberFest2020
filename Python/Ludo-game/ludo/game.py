from collections import namedtuple, deque
import random
from .painter import PaintBoard

# Thanks to Angel Angelov
# This is piece or a token in ludo game
# Simple class has only index, colour and id attributes
Pawn = namedtuple("Pawn", "index colour id")


class Player():
   
    def __init__(self, colour, name=None, choose_pawn_delegate=None):
       
        self.colour = colour
        self.choose_pawn_delegate = choose_pawn_delegate
        self.name = name
        if self.name is None and self.choose_pawn_delegate is None:
            self.name = "computer"
        self.finished = False
        # initialize four pawns with
        # id (first leter from colour and index (from 1 to 4))
        self.pawns = [Pawn(i, colour, colour[0].upper() + str(i))
                      for i in range(1, 5)]

    def __str__(self):
        return "{}({})".format(self.name, self.colour)

    def choose_pawn(self, pawns):
        
        if len(pawns) == 1:
            index = 0
        elif len(pawns) > 1:
            if self.choose_pawn_delegate is None:
                index = random.randint(0, len(pawns) - 1)
            else:
                index = self.choose_pawn_delegate()
        return index


class Board():
  
    # common (shared) squares for all pawns
    BOARD_SIZE = 56

    # save (private) positions (squares) for each colour
    # This is squares just before pawn finished
    BOARD_COLOUR_SIZE = 7

    COLOUR_ORDER = ['yellow', 'blue', 'red', 'green']

    # distance between two neighbour colours
    # (The distance from start square of one colour
    # to start square of next colour)
    COLOUR_DISTANCE = 14

    def __init__(self):
        #fn1353c
        # get dict of start position for every colour
        Board.COLOUR_START = {
            colour: 1 + index * Board.COLOUR_DISTANCE for
            index, colour in enumerate(Board.COLOUR_ORDER)}
        # get dict of end position for every colour
        Board.COLOUR_END = {
            colour: index * Board.COLOUR_DISTANCE
            for index, colour in enumerate(Board.COLOUR_ORDER)}
        Board.COLOUR_END['yellow'] = Board.BOARD_SIZE

        # dict where key is pawn and
        # value is two size tuple holds position
        # Position is combination of
        # common (share) square and coloured (private) square.
        self.pawns_possiotion = {}

        # painter is used to visually represent
        # the board and position of the pawns
        self.painter = PaintBoard()

        # pool means before start1353
        self.board_pool_position = (0, 0)

    def set_pawn(self, pawn, position):
        
        self.pawns_possiotion[pawn] = position

    def put_pawn_on_board_pool(self, pawn):
        self.set_pawn(pawn, self.board_pool_position)

    def is_pawn_on_board_pool(self, pawn):
       
        return self.pawns_possiotion[pawn] == self.board_pool_position

    def put_pawn_on_starting_square(self, pawn):
        start = Board.COLOUR_START[pawn.colour.lower()]
        position = (start, 0)
        self.set_pawn(pawn, position)

    def can_pawn_move(self, pawn, rolled_value):
       
        common_poss, private_poss = self.pawns_possiotion[pawn]
        if private_poss + rolled_value > self.BOARD_COLOUR_SIZE:
            return False
        return True

    def move_pawn(self, pawn, rolled_value):
        
        common_poss, private_poss = self.pawns_possiotion[pawn]
        end = self.COLOUR_END[pawn.colour.lower()]
        if private_poss > 0:
            # pawn is already reached own final squares
            private_poss += rolled_value
        elif common_poss <= end and common_poss + rolled_value > end:
            # pawn is entering in own squares
            private_poss += rolled_value - (end - common_poss)
            common_poss = end
        else:
            # pawn will be still in common square
            common_poss += rolled_value
            if common_poss > self.BOARD_SIZE:
                common_poss = common_poss - self.BOARD_SIZE
        position = common_poss, private_poss
        self.set_pawn(pawn, position)

    def does_pawn_reach_end(self, pawn):
        
        common_poss, private_poss = self.pawns_possiotion[pawn]
        if private_poss == self.BOARD_COLOUR_SIZE:
            return True
        return False

    def get_pawns_on_same_postion(self, pawn):
        
        position = self.pawns_possiotion[pawn]
        return [curr_pawn for curr_pawn, curr_postion in
                self.pawns_possiotion.items()
                if position == curr_postion]

    def paint_board(self):
        
        positions = {}
        for pawn, position in self.pawns_possiotion.items():
            common, private = position
            if not private == Board.BOARD_COLOUR_SIZE:
                positions.setdefault(position, []).append(pawn)
        return self.painter.paint(positions)


class Die():

    MIN = 1
    MAX = 6

    @staticmethod
    def throw():
        return random.randint(Die.MIN, Die.MAX)


class Game():
   

    def __init__(self):
        self.players = deque()
        self.standing = []
        self.board = Board()
        # is game finished
        self.finished = False
        # last rolled value from die (dice)
        self.rolled_value = None
        # player who last rolled die
        self.curr_player = None
        # curr_player's possible pawn to move
        self.allowed_pawns = []
        # curr_player's chosen pawn to move
        self.picked_pawn = None
        # chosen index from allowed pawn 
        self.index = None
        # jog pawn if any 
        self.jog_pawns = []

    def add_palyer(self, player):
        self.players.append(player)
        for pawn in player.pawns:
            self.board.put_pawn_on_board_pool(pawn)

    def get_available_colours(self):
       
        used = [player.colour for player in self.players]
        available = set(self.board.COLOUR_ORDER) - set(used)
        return sorted(available)

    def _get_next_turn(self):
       
        if not self.rolled_value == Die.MAX:
            self.players.rotate(-1)
        return self.players[0]

    def get_pawn_from_board_pool(self, player):
       
        for pawn in player.pawns:
            if self.board.is_pawn_on_board_pool(pawn):
                return pawn

    def get_allowed_pawns_to_move(self, player, rolled_value):
        
        allowed_pawns = []
        if rolled_value == Die.MAX:
            pawn = self.get_pawn_from_board_pool(player)
            if pawn:
                allowed_pawns.append(pawn)
        for pawn in player.pawns:
            if not self.board.is_pawn_on_board_pool(pawn) and\
                    self.board.can_pawn_move(pawn, rolled_value):
                allowed_pawns.append(pawn)
        return sorted(allowed_pawns, key=lambda pawn: pawn.index)

    def get_board_pic(self):
        return self.board.paint_board()

    def _jog_foreign_pawn(self, pawn):
        pawns = self.board.get_pawns_on_same_postion(pawn)
        for p in pawns:
            if p.colour != pawn.colour:
                self.board.put_pawn_on_board_pool(p)
                self.jog_pawns.append(p)

    def _make_move(self, player, pawn):
       
        if self.rolled_value == Die.MAX and\
                self.board.is_pawn_on_board_pool(pawn):
            self.board.put_pawn_on_starting_square(pawn)
            self._jog_foreign_pawn(pawn)
            return
        self.board.move_pawn(pawn, self.rolled_value)
        if self.board.does_pawn_reach_end(pawn):
            player.pawns.remove(pawn)
            if not player.pawns:
                self.standing.append(player)
                self.players.remove(player)
                if len(self.players) == 1:
                    self.standing.extend(self.players)
                    self.finished = True
        else:
            self._jog_foreign_pawn(pawn)

    def play_turn(self, ind=None, rolled_val=None):
        
        self.jog_pawns = []
        self.curr_player = self._get_next_turn()
        if rolled_val is None:
            self.rolled_value = Die.throw()
        else:
            self.rolled_value = rolled_val
        self.allowed_pawns = self.get_allowed_pawns_to_move(
            self.curr_player, self.rolled_value)
        if self.allowed_pawns:
            if ind is None:
                self.index = self.curr_player.choose_pawn(
                    self.allowed_pawns)
            else:
                self.index = ind
            self.picked_pawn = self.allowed_pawns[self.index]
            self._make_move(self.curr_player, self.picked_pawn)
        else:
            self.index = -1
            self.picked_pawn = None
