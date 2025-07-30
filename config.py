import rtoml
from typing import List, Dict, Any
import os

class GameConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
    
    def _load_config(self) -> List[Dict[str, Any]]:
        """实时读取配置文件（无缓存）"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return rtoml.loads(content).get("game", [])
            else:
                print(f"配置文件 {self.config_path} 不存在")
                return []
        except Exception as e:
            print(f"读取配置失败: {e}")
            return []
    
    def get_games(self) -> List[Dict[str, Any]]:
        """获取所有游戏配置（实时读取）"""
        return self._load_config()
    
    def get_game_by_id(self, game_id: int) -> Dict[str, Any]:
        """通过ID获取单个游戏配置（实时读取）"""
        games = self._load_config()
        for game in games:
            if int(game.get("id", -1)) == int(game_id):
                return game
        return {}
    
    def get_keymaps(self, game_id: int) -> List[Dict[str, str]]:
        """获取指定游戏的按键映射（实时读取）"""
        game = self.get_game_by_id(game_id)
        return game.get("key_map", [])
    
    def save_config(self, games_list: List[Dict[str, Any]]) -> bool:
        """保存配置（直接写入目标文件）"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                rtoml.dump({"game": games_list}, f)
            print(f"配置已保存到 {self.config_path}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False