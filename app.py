import pyxel
import random

# 定数定義
SCREEN_WIDTH = 200 # ウィンドウの幅（ピクセル単位）
SCREEN_HEIGHT = 240 # ウィンドウの高さ（ピクセル単位）
GRID_WIDTH = 10 # ゲームフィールドの横幅（グリッド数）
GRID_HEIGHT = 20 # ゲームフィールドの高さ（グリッド数）
CELL_SIZE = 10 # 各グリッドのサイズ（ピクセル単位）
BLOCK_GAME_SHOW_COUNT = 3000 # ブロックゲームの表示時間（ミリ秒）
IS_DEBUG = False # デバッグモード

# ブロックピースの形状と色
# SEE: https://ja.wikipedia.org/wiki/%E3%83%86%E3%83%88%E3%83%AD%E3%83%9F%E3%83%8E
class Shapre:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class BlockPiece:
    def __init__(self, shape, color):
        self.shape = shape
        self.color = color

BLOCKS = [
    BlockPiece([[1, 1, 1, 1]], 8), # I型ブロックピース
    BlockPiece([[1, 1], [1, 1]], 9), # O型ブロックピース
    BlockPiece([[0, 1, 1], [1, 1, 0]], 10), # S型ブロックピース
    BlockPiece([[1, 1, 0], [0, 1, 1]], 11), # Z型ブロックピース
    BlockPiece([[1, 0, 0], [1, 1, 1]], 12), # J型ブロックピース
    BlockPiece([[0, 0, 1], [1, 1, 1]], 13), # L型ブロックピース
    BlockPiece([[0, 1, 0], [1, 1, 1]], 14), # T型ブロックピース
]

# img = pyxel.Image(32, 32)
# img.load(x=0, y=0, filename='kurokokun.png')

# パク...参考にさせていただきました。: https://note.com/kkuboya/n/na05766030f20
class BlockGame:
    def __init__(self):
        """
        ゲームの初期化
        """
        # Pyxelの初期化
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT)

        # ゲーム状態を管理する変数
        self.state = "TITLE"  # 初期状態はタイトル画面

        # ゲームを初期状態に
        self.reset()

        # ゲームループを開始
        pyxel.run(self.update, self.draw)

    def update(self):
        """
        ゲームロジックの更新
        """
        if self.state == "TITLE": # タイトル画面
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A): # エンターキーでゲーム開始
                self.state = "PLAYING"
            return

        if self.state == "GAMEOVER": # ゲームオーバー画面
            if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_GUIDE): # Rキーでリスタート
                self.reset()
                self.state = "PLAYING"
            return
        
        # 以降はゲームプレイ中の処理
        # TODO: ボタンの同時押し時に問題が出ないか？

        # 基本操作
        # TODO: 足掻くような動きを実現する場合、ボタン押下時に一旦returnしてlock_pieceが呼ばれないようにした方が良い？
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT): # 左移動
            if not self.check_collision(self.current_x - 1, self.current_y, self.current_piece.shape):
                self.current_x -= 1
        if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT): # 右移動
            if not self.check_collision(self.current_x + 1, self.current_y, self.current_piece.shape):
                self.current_x += 1

        if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN): # 下移動（高速落下）
            if not self.check_collision(self.current_x, self.current_y + 1, self.current_piece.shape):
                self.current_y += 1
            else:
                self.lock_piece()
                self.spawn_new_piece()

        # 特殊操作
        if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP): # 即時落下（上キー）
            # コリジョンが発生するまで下に持っていく。
            while not self.check_collision(self.current_x, self.current_y + 1, self.current_piece.shape):
                self.current_y += 1
            self.lock_piece()
            self.spawn_new_piece()

        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A): # 回転
            rotated_piece = self.rotate_piece()
            if not self.check_collision(self.current_x, self.current_y, rotated_piece):
                self.current_piece.shape = rotated_piece
                # TODO: 回転効果音
        
        if pyxel.btnp(pyxel.KEY_SHIFT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B): # ホールド
            self.hold()

        # 自然落下の処理
        if pyxel.frame_count % self.drop_interval == 0:
            if self.check_collision(self.current_x, self.current_y + 1, self.current_piece.shape):
                self.lock_piece()
                self.spawn_new_piece()
            else:
                self.current_y += 1

    def draw(self):
        """
        画面の描画処理
        """
        pyxel.cls(0) # 画面クリア。チラつかないのはなぜかよくわからない。pyxelがダブルバッファリングしてるとか？

        # 状態ごとに描画処理を分岐
        # FIXME: レンダリングプロセスを大まかに分離

        # ゲーム画面
        if self.state == "PLAYING":
            self.draw_grid() # フィールドを描画
            self.draw_piece_shadow(self.current_piece, self.current_x, self.current_y) # 現在のピースの影を描画（現在のピースと被った場合に上書きするため先に実行）
            self.draw_piece(self.current_piece, self.current_x, self.current_y) # 現在のピースを描画
            self.draw_ui() # UIを描画
            # print(self.grid)
            return

        # TODO: サンプルを参考にしたがこのやり方が良いのか？
        # タイトル画面
        # FIXME: 文字列の中心を中心に添えたいが...
        if self.state == "TITLE":
            title_x = SCREEN_WIDTH // 2 - 40
            title_y = SCREEN_HEIGHT // 2 - 10
            # pyxel.text(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 10, "BLOCK_GAME", pyxel.COLOR_YELLOW) # JSのMath.floorの代わりに//を使用する
            pyxel.text(title_x, title_y, f"B", pyxel.COLOR_RED)
            pyxel.text(title_x + 10, title_y, f"L", pyxel.COLOR_ORANGE)
            pyxel.text(title_x + 20, title_y, f"O", pyxel.COLOR_YELLOW)
            pyxel.text(title_x + 30, title_y, f"C", pyxel.COLOR_GREEN)
            pyxel.text(title_x + 40, title_y, f"K", pyxel.COLOR_LIGHT_BLUE)
            pyxel.text(title_x + 50, title_y, f"S", pyxel.COLOR_PURPLE)
            pyxel.text(title_x + 60, title_y, f"!", pyxel.COLOR_PINK)
            pyxel.text(SCREEN_WIDTH // 2 - 60, title_y + 10, "Press ENTER to Start", pyxel.COLOR_WHITE)
            # pyxel.blt(SCREEN_WIDTH // 2 - 80, title_y + 20, img, 0, 0, img.width, img.height)
            return

        # ゲームオーバー画面
        if self.state == "GAMEOVER":
            pyxel.text(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 10, "GAME OVER", pyxel.COLOR_RED)
            pyxel.text(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 10, f"Score: {self.score}", pyxel.COLOR_WHITE)
            pyxel.text(SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2, "Press R to Restart", pyxel.COLOR_WHITE)
            # pyxel.blt(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2, img, 0, 0, img.width, img.height)
            return

    def reset(self) -> None:
        """
        ゲーム関連の値を初期状態にリセットする。
        """
        self.grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)] # フィールドを初期化
        self.current_piece = self.get_new_piece() # 現在操作するブロックピースを生成
        self.next_piece = self.get_new_piece() # 次のブロックピースを生成
        self.hold_piece = None # ホールドされているブロックピース
        self.can_hold = True # ホールド可能フラグ
        self.current_x = GRID_WIDTH // 2 - len(self.current_piece.shape[0]) // 2 # 現在のピースのx座標（中央揃え）
        self.current_y = 0 # 現在のピースのy座標（上端）
        self.score = 0 # スコア
        self.level = 1 # 現在のレベル
        self.lines_cleared = 0 # 消去したライン数
        self.drop_interval = 30 # ピースの落下間隔（フレーム数）
        self.game_over = False # ゲームオーバー判定
        self.block_game_show_count = 0 if not IS_DEBUG else 3000 # 4ライン同時消し時の表示カウンタ

    def get_new_piece(self) -> BlockPiece:
        """
        ランダムに新しいブロックピースを取得
        """
        return random.choice(BLOCKS)

    def rotate_piece(self) -> list:
        """
        現在のブロックピースを右方向に90度回転した形状を返す\n
        以下処理の流れ\n
        [\n
          [0, 1, 1],\n
          [1, 1, 0],\n
        ]\n
        ↓ [::1]配列を反転させる\n
        [\n
          [1, 1, 0],\n
          [0, 1, 1],\n
        ]\n
        ↓ zip([1, 1, 0], [0, 1, 1]) zipで分解した1次元配列から要素を取り出し、それをリストにして返すことで90度回転させる\n
        [\n
          (1, 0),\n
          (1, 1),\n
          (0, 1) \n
        ]\n
        """
        # 高校の時にIT簿記選手権でやったのを思い出した。擬似言語だったのでzipは使えず地道にやったはず...
        return [list(row) for row in zip(*self.current_piece.shape[::-1])]

    def check_collision(self, x, y, piece_shape) -> bool:
        """
        指定された位置にブロックピースを配置可能か確認\n
        ※ 実際の衝突判定は現在の位置ではなく、これから配置する位置に対して行うこと。
        """
        for row_idx, row in enumerate(piece_shape):
            for col_idx, cell in enumerate(row):
                if cell: 
                    # ブロックピースのブロック部分
                    grid_x = x + col_idx
                    grid_y = y + row_idx

                    # グリッド外や既存のブロックとの衝突を確認
                    # TODO: 衝突効果音？
                    if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y >= GRID_HEIGHT:
                        return True
                    if grid_y >= 0 and self.grid[grid_y][grid_x]:
                        return True
        return False

    def lock_piece(self) -> None:
        """
        現在のブロックピースをフィールドに固定
        """
        for row_idx, row in enumerate(self.current_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell: 
                    # ブロック部分を固定
                    self.grid[self.current_y + row_idx][self.current_x + col_idx] = self.current_piece.color
                    # TODO: ブロック設置効果音
        self.clear_lines()

    def clear_lines(self) -> None:
        """
        フィールド上の揃ったラインを消去
        """
        new_grid = [row for row in self.grid if any(cell == 0 for cell in row)] # 揃っていない行を残す
        cleared_line_count = GRID_HEIGHT - len(new_grid) # 消去された行数

        # TODO: 4行以上同時に消去された場合の処理（ブロックゲーム！）
        if cleared_line_count == 4:
            self.block_game_show_count = BLOCK_GAME_SHOW_COUNT
            # TODO: ブロックゲーム効果音

        self.lines_cleared += cleared_line_count
        self.score += cleared_line_count * 100 * self.level # スコア加算
        new_grid = [[0] * GRID_WIDTH for _ in range(cleared_line_count)] + new_grid # 新しいフィールドを作成
        self.grid = new_grid

        # レベルアップ処理
        if self.lines_cleared >= self.level * 5:
            self.level += 1
            self.drop_interval = max(5, self.drop_interval - 2) # 落下速度を高速化

    def hold(self) -> None:
        """
        現在のブロックピースをホールドする
        """
        if not self.can_hold: # 1回のピース操作で1度しかホールドできないように
            return
        if self.hold_piece is None: # 初回のホールド
            self.hold_piece = self.current_piece
            self.spawn_new_piece()
        else: # 既存のホールドピースと交換
            self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
        self.current_x = GRID_WIDTH // 2 - len(self.current_piece.shape[0]) // 2
        self.current_y = 0
        self.can_hold = False # ホールドを連打されると困るので、1回の操作で1度しかホールドできないようにフラグで管理することにした。

    def spawn_new_piece(self) -> None:
        """
        次のブロックピースを生成して配置
        """
        self.current_piece = self.next_piece
        self.next_piece = self.get_new_piece()
        self.current_x = GRID_WIDTH // 2 - len(self.current_piece.shape[0]) // 2
        self.current_y = 0
        self.can_hold = True
        # 新しいピースが即座に衝突する場合、ゲームオーバー
        if self.check_collision(self.current_x, self.current_y, self.current_piece.shape):
            self.game_over = True
            self.state = "GAMEOVER"
    
    def get_shadow_color(self, color) -> int:
        """
        ブロックピースの影の色を取得
        """
        # FIXME: 生成AIに生成させたが色がイメージと違う
        return {
            8 : 5, # I -> 暗い水色
            9 : 6, # O -> 暗い黄色
            10: 3, # S -> 暗い緑
            11: 1, # Z -> 暗い赤
            12: 4, # L -> 暗いオレンジ
            13: 7, # J -> 暗い青
            14: 2, # T -> 暗い紫
        }.get(color, pyxel.COLOR_GRAY)

    def draw_grid(self) -> None:
        """
        フィールドおよび固定されたブロックピースを描画
        """
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                cell = self.grid[y][x]
                if cell: # ブロックが存在する場合のみ描画
                    pyxel.rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, cell)
                pyxel.rectb(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, 1) # TODO: 固定ずみのブロックピースには枠線を表示

    def draw_piece(self, piece, x_offset, y_offset) -> None:
        """
        ブロックピースを描画
        """
        for row_idx, row in enumerate(piece.shape):
            for col_idx, cell in enumerate(row):
                if cell: # ブロック部分を描画
                    x = (x_offset + col_idx) * CELL_SIZE
                    y = (y_offset + row_idx) * CELL_SIZE
                    pyxel.rect(x, y, CELL_SIZE, CELL_SIZE, piece.color)

    def draw_piece_shadow(self, piece, x_offset, y_offset) -> None:
        """
        ブロックピースの影を描画
        """
        # TODO: ブロックピースの座標から、そのブロックピースが着地する位置までの距離を計算して、その位置に影を描画する
        shadow_y = y_offset
        while not self.check_collision(self.current_x, shadow_y + 1, self.current_piece.shape):
            shadow_y += 1

        for row_idx, row in enumerate(piece.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    x = (x_offset + col_idx) * CELL_SIZE
                    y = (shadow_y + row_idx) * CELL_SIZE
                    # FIXME: 影っぽい表現
                    shadow_color = self.get_shadow_color(piece.color)
                    pyxel.rect(x, y, CELL_SIZE, CELL_SIZE, shadow_color)
        

    def draw_ui(self) -> None:
        """
        スコアや次のピース、ホールド情報などのUIを描画
        """
        # NEXT, HOLD
        pyxel.text(120, 5, "NEXT", pyxel.COLOR_WHITE)
        self.draw_piece(self.next_piece, 17, 1)

        pyxel.text(120, 50, "HOLD", pyxel.COLOR_WHITE)
        if self.hold_piece:
            self.draw_piece(self.hold_piece, 17, 5)

        # スコア表示
        pyxel.text(120, 100, f"Score: {self.score}", pyxel.COLOR_WHITE)
        pyxel.text(120, 110, f"Level: {self.level}", pyxel.COLOR_WHITE)
        pyxel.text(120, 120, f"Lines: {self.lines_cleared}", pyxel.COLOR_WHITE)
        
        if(IS_DEBUG): # デバッグモード
            pyxel.text(120, 130, f"BLOCK_GAME_SHOW_COUNT: {self.block_game_show_count}", pyxel.COLOR_WHITE)
        if(self.block_game_show_count > 0):
            pyxel.text(120, 130, f"B", pyxel.COLOR_RED)
            pyxel.text(130, 130, f"L", pyxel.COLOR_ORANGE)
            pyxel.text(140, 130, f"O", pyxel.COLOR_YELLOW)
            pyxel.text(150, 130, f"C", pyxel.COLOR_GREEN)
            pyxel.text(160, 130, f"K", pyxel.COLOR_LIGHT_BLUE)
            pyxel.text(160, 130, f"S", pyxel.COLOR_PURPLE)
            pyxel.text(170, 130, f"!", pyxel.COLOR_PINK)
            self.block_game_show_count -= 1

        # キー操作説明
        pyxel.text(120, 140, f"CONTROLES GUIDE", pyxel.COLOR_LIME)
        pyxel.text(120, 150, f"UP KEY: hard drop", pyxel.COLOR_WHITE)
        pyxel.text(120, 160, f"DOWN KEY: soft drop", pyxel.COLOR_WHITE)
        pyxel.text(120, 170, f"SPACE KEY or A BUTTON: rotate", pyxel.COLOR_WHITE)
        pyxel.text(120, 180, f"SHIFT KEY or B BUTTON: hold/release", pyxel.COLOR_WHITE)


if __name__ == "__main__":
    BlockGame()
