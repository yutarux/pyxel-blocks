pyxelで作る某パズルゲームもどき
===

### 実行方法
```bash
pip install -r requirements.txt
python app.py
```

### ビルド方法
* pyxelパッケージを生成する場合
    ```bash
    pyxel package ../pyxel-blocks ../pyxel-blocks/app.py
    ```
* html形式で実行したい場合
  * 事前にpyxelパッケージを生成しておく必要があります。
    ```bash
    pyxel app2html pyxel-blocks.pyxapp
    ```
  * バイナリ及び実行環境（のCDNリンク）が含まれたhtmlファイルが生成されるので、そのまま実行可能
 
### 今後の課題
- TODO リスト
    - [ ] ブロック回転時の回転軸の考慮
    - [ ] デプロイ時に自動ビルドを行い、pagesとして公開
    - [ ] BGMの追加
    - [ ] 効果音の追加
    - [ ] 全体的なUIの微調整
    - [ ] 何かユニークなギミックを...