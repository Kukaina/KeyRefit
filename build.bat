cd ./UI/keyrefit_ui/
call pnpm run build
xcopy "./dist" "../../vue_dist" /e /i /q /r /y
cd ../../
call uv run main.py