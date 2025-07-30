<template>
    <n-dialog-provider>
        <n-grid x-gap="12" :cols="24" style="height: 868px;">
            <n-gi :span="6" :offset="1">
                <n-list hoverable clickable style="height: 100%;">
                    <template #header>
                        <span style="font-weight: bolder; font-size: large; color: #303133;">配置列表</span>
                    </template>
                    <n-scrollbar style="max-height:338px">
                        <n-list-item v-for="data in datum" :key="data.id" class="list_name" @click="get_data_now(data.id)"
                            :class="{ active: data.id === selectedItem }">
                            <n-ellipsis style="max-width:200px">{{ data.name }}</n-ellipsis>
                        </n-list-item>
                    </n-scrollbar>
                    <template #footer>
                        <n-button secondary strong size="large" style="width: 100%;" type="success"
                            @click="showAddConfigDialog">添加配置</n-button>
                        <n-button type="error" style="width: 100%;margin-top: 4px;" secondary strong size="large"
                            @click="deleteCurrentConfig()">删除配置</n-button>
                    </template>
                </n-list>
            </n-gi>

            <n-gi :span="14" :offset="1">
                <div v-if="data_now">
                    <n-card style="margin-top: 12px; height: 432px; position: relative;" embedded :bordered="false">
                        <div class="mb-2">
                            <n-input-group>
                                <n-input v-model:value="editedName" :disabled="!editingName">
                                    <template #prefix>
                                        <span style="margin-right: 6px; background-color: #FAFAFC;">游戏名称:</span>
                                    </template>
                                </n-input>
                                <n-button @click="toggleEdit('name')">
                                    {{ editingName ? '保存' : '编辑' }}
                                </n-button>
                            </n-input-group>

                            <n-input-group style="margin-top: 4px;">
                                <n-input v-model:value="editedWindowName" :disabled="!editingWindowName">
                                    <template #prefix>
                                        <span style="margin-right: 6px; background-color: #FAFAFC;">游戏窗口名称:</span>
                                    </template>
                                </n-input>
                                <n-button @click="toggleEdit('window_name')">
                                    {{ editingWindowName ? '保存' : '编辑' }}
                                </n-button>
                            </n-input-group>

                        </div>

                        <div>
                            <span
                                style="font-weight: bold; margin-top: 12px; margin-bottom: 6px; font-size: large; display: block;">键位映射:</span>
                            <n-scrollbar style="max-height: 320px;">
                                <div>
                                    <div v-for="(value, key) in data_now.key_map" :key="key" style="margin-bottom: 4px;">
                                        <n-button secondary type="info" @click="editMapping('key', key, value)">
                                            {{ displayKeyName(key) }}
                                        </n-button>
                                        <span style="margin: 0 8px;">映射为</span>
                                        <n-button secondary type="info" @click="editMapping('value', key, value)">
                                            {{ displayKeyName(value) }}
                                        </n-button>
                                    </div>
                                </div>
                            </n-scrollbar>
                        </div>
                        <n-float-button-group style="position: absolute; bottom: 16px; right: 16px;">
                            <n-float-button type="primary" @click="addMapping" :tooltip="'添加按键映射'">
                                <n-icon>
                                    <AddSharp></AddSharp>
                                </n-icon>
                            </n-float-button>
                            <n-tooltip trigger="hover" placement="bottom">
                                <template #trigger>
                                    <n-float-button @click="toggleStrictMode()">
                                        <n-icon :tooltip="exact_match">
                                            <LockOpenSharp v-if="!exact_match.value"></LockOpenSharp>
                                            <LockClosedSharp v-else></LockClosedSharp>
                                        </n-icon>
                                    </n-float-button>
                                </template>
                                是否开启窗口严格匹配,目前为{{ exact_match }}
                            </n-tooltip>
                        </n-float-button-group>
                    </n-card>

                    <n-button @click="hookHandle(data_now.id)" style="width: 100%;margin-top: 4px;" :loading="loading">
                        {{ hookstart ? '停止映射' : '启动映射' }}
                    </n-button>
                </div>

                <div v-else class="text-gray-500 italic mt-4">请从左侧选择一个配置项</div>
            </n-gi>

        </n-grid>

    </n-dialog-provider>
</template>
  
  
<script setup>
import { AddSharp, LockOpenSharp, LockClosedSharp } from "@vicons/ionicons5";
import {
    ref,
    computed,
    watch,
    onMounted,
    h,
} from "vue";
import {
    useDialog,
    NButton,
    NTreeSelect,
    NSpace,
    NInput
} from "naive-ui";


const exact_match = ref(true)
const hookstart = ref(false)
const editingName = ref(false);
const editingWindowName = ref(false);
const editedName = ref('');
const editedWindowName = ref('');
const datum = ref([]); // 真实配置加载后赋值
const loading = ref(false);
const selectedItem = ref(null);
const dialog = useDialog();

// 按键名称映射，用于友好显示
const keyDisplayNameMap = {
    Space: "空格",
    Enter: "回车",
    Escape: "Esc",
    ArrowUp: "Up",
    ArrowDown: "Down",
    ArrowLeft: "Left",
    ArrowRight: "Right",
    Shift: "Shift",
    Control: "Ctrl",
    Alt: "Alt",
    CapsLock: "CapsLock",
    Tab: "Tab",
    Backspace: "Backspace",
    Insert: "Insert",
    Delete: "Delete",
    Home: "Home",
    End: "End",
    PageUp: "PageUp",
    PageDown: "PageDown",
    NumLock: "NumLock",
    PrintScreen: "PrintScreen",
    ScrollLock: "ScrollLock",
    Pause: "Pause",
    ContextMenu: "Apps",
};

// 转换键名到后端规范名
function convertKeyToBackendName(key) {
    if (!key) return "";
    if (keyDisplayNameMap[key]) return keyDisplayNameMap[key];
    if (/^F\d{1,2}$/.test(key)) return key;
    if (/^Numpad\d$/.test(key)) return key;
    if (key.length === 1) {
        const upper = key.toUpperCase();
        if (upper >= "A" && upper <= "Z") return upper;
        if (upper >= "0" && upper <= "9") return upper;
    }
    if (key === "ArrowUp") return "Up";
    if (key === "ArrowDown") return "Down";
    if (key === "ArrowLeft") return "Left";
    if (key === "ArrowRight") return "Right";
    return key;
}

// 树形选择键位选项
const treeOptions = [
    {
        label: "字母区",
        key: "letters",
        children: Array.from({ length: 26 }, (_, i) => ({
            label: String.fromCharCode(65 + i),
            key: String.fromCharCode(65 + i),
            isLeaf: true,
        })),
    },
    {
        label: "数字区",
        key: "numbers",
        children: Array.from({ length: 10 }, (_, i) => ({
            label: String(i),
            key: String(i),
            isLeaf: true,
        })),
    },
    {
        label: "功能键",
        key: "function_keys",
        children: Array.from({ length: 12 }, (_, i) => {
            const fkey = `F${i + 1}`;
            return { label: fkey, key: fkey, isLeaf: true };
        }),
    },
    {
        label: "方向键",
        key: "arrows",
        children: [
            { label: "Up", key: "Up", isLeaf: true },
            { label: "Down", key: "Down", isLeaf: true },
            { label: "Left", key: "Left", isLeaf: true },
            { label: "Right", key: "Right", isLeaf: true },
        ],
    },
    {
        label: "特殊键",
        key: "special",
        children: [
            { label: "Esc", key: "Esc", isLeaf: true },
            { label: "Tab", key: "Tab", isLeaf: true },
            { label: "CapsLock", key: "CapsLock", isLeaf: true },
            { label: "Shift", key: "Shift", isLeaf: true },
            { label: "Ctrl", key: "Ctrl", isLeaf: true },
            { label: "Alt", key: "Alt", isLeaf: true },
            { label: "Space", key: "Space", isLeaf: true },
            { label: "Enter", key: "Enter", isLeaf: true },
            { label: "Backspace", key: "Backspace", isLeaf: true },
            { label: "Insert", key: "Insert", isLeaf: true },
            { label: "Delete", key: "Delete", isLeaf: true },
            { label: "Home", key: "Home", isLeaf: true },
            { label: "End", key: "End", isLeaf: true },
            { label: "PageUp", key: "PageUp", isLeaf: true },
            { label: "PageDown", key: "PageDown", isLeaf: true },
            { label: "NumLock", key: "NumLock", isLeaf: true },
            { label: "PrintScreen", key: "PrintScreen", isLeaf: true },
            { label: "ScrollLock", key: "ScrollLock", isLeaf: true },
            { label: "Pause", key: "Pause", isLeaf: true },
            { label: "Apps", key: "Apps", isLeaf: true },
            { label: "LWin", key: "LWin", isLeaf: true },
            { label: "RWin", key: "RWin", isLeaf: true },
        ],
    },
    {
        label: "小键盘",
        key: "numpad",
        children: [
            { label: "Numpad0", key: "Numpad0", isLeaf: true },
            { label: "Numpad1", key: "Numpad1", isLeaf: true },
            { label: "Numpad2", key: "Numpad2", isLeaf: true },
            { label: "Numpad3", key: "Numpad3", isLeaf: true },
            { label: "Numpad4", key: "Numpad4", isLeaf: true },
            { label: "Numpad5", key: "Numpad5", isLeaf: true },
            { label: "Numpad6", key: "Numpad6", isLeaf: true },
            { label: "Numpad7", key: "Numpad7", isLeaf: true },
            { label: "Numpad8", key: "Numpad8", isLeaf: true },
            { label: "Numpad9", key: "Numpad9", isLeaf: true },
            { label: "NumpadMultiply", key: "NumpadMultiply", isLeaf: true },
            { label: "NumpadAdd", key: "NumpadAdd", isLeaf: true },
            { label: "NumpadSeparator", key: "NumpadSeparator", isLeaf: true },
            { label: "NumpadSubtract", key: "NumpadSubtract", isLeaf: true },
            { label: "NumpadDecimal", key: "NumpadDecimal", isLeaf: true },
            { label: "NumpadDivide", key: "NumpadDivide", isLeaf: true },
        ],
    },
];
//启动按钮
const hookHandle = async (id) => {
    if (loading.value) return;
    loading.value = true;

    try {
        let result;
        if (!hookstart.value) {
            // 启动逻辑（保持不变）
            console.log("正在启动映射");

            result = await pywebview.api.start_hook(parseInt(id), exact_match.value);
            console.log(result);

        } else {
            // 停止逻辑：设置超时（5秒）
            result = await Promise.race([
                pywebview.api.stop_hook(),
                new Promise((_, reject) => {
                    setTimeout(() => reject(new Error("停止超时")), 5000);
                })
            ]);
        }

        // 处理结果（保持不变）
        if (result) {
            hookstart.value = !hookstart.value;
        } else {
            alert("操作失败");
        }
    } catch (e) {
        console.error("操作失败:", e);
        alert("操作失败: " + e.message);
    } finally {
        loading.value = false; // 无论成功/失败/超时，都结束loading
    }
};
// 计算当前选中项数据
const data_now = computed(() => {
    if (!selectedItem.value) return null;
    return datum.value.find(item => item.id === selectedItem.value);
});

const loadGames = async () => {
    try {
        if (!pywebview || !pywebview.api) {
            throw new Error('pywebview API 不存在');
        }
        const games = await pywebview.api.get_games();
        console.log(games);

        datum.value = games.map(game => ({
            id: String(game.id),
            name: game.name,
            window_name: game.window_title || game.window_name || "",
            key_map: game.key_map
        }));
        games.forEach((i) => console.log(i.key_map))
        if (datum.value.length > 0) {
            selectedItem.value = datum.value[0].id;
        }
        console.log(games);
        console.log(datum.value);
    } catch (e) {
        // console.error('加载游戏配置失败:', e);
        console.log("lg", e);
    }
}

onMounted(() => {
    window.addEventListener('pywebviewready', function () {
        loadGames().catch(err => {
            console.error('启动时游戏配置加载失败:', err);
        });
    })
    if (!localStorage.getItem("exact_match")) {
        localStorage.setItem("exact_match", true)
    }
    exact_match.value = localStorage.getItem("exact_match")


});

// 监听data_now变化，同步编辑框内容与编辑状态
watch(data_now, (newVal) => {
    if (newVal) {
        editedName.value = newVal.name;
        editedWindowName.value = newVal.window_name;
        editingName.value = false;
        editingWindowName.value = false;
    }
}, { immediate: true });

// 监听选中项，保存到本地存储
watch(selectedItem, (newVal) => {
    if (newVal) {
        localStorage.setItem("selectedid", newVal);
    } else {
        localStorage.removeItem("selectedid");
    }
});

function get_data_now(id) {
    selectedItem.value = id;
}

function toggleEdit(type) {
    if (type === 'name') {
        if (editingName.value) {
            if (data_now.value) {
                data_now.value.name = editedName.value.trim() || data_now.value.name;
            }
            save()
            editingName.value = false;
        } else {
            editingName.value = true;
        }
    } else if (type === 'window_name') {
        if (editingWindowName.value) {
            if (data_now.value) {
                data_now.value.window_name = editedWindowName.value.trim() || data_now.value.window_name;
                datum.value.forEach(element => {
                    if (element.id === data_now.id) {
                        element = data_now
                    }
                });
                console.log(datum.value);
                pywebview.api.save_config(datum.value)
            }
            save()
            editingWindowName.value = false;
        } else {
            editingWindowName.value = true;
        }
    }
}

function displayKeyName(key) {
    return keyDisplayNameMap[key] || key;
}

// --- 编辑映射 Dialog ---
function editMapping(type, key, value) {
    const listening = ref(false);
    const selectedKey = ref(type === "key" ? key : value);
    const capturedKey = ref("");

    function startListen() {
        if (listening.value) return;
        listening.value = true;
        window.addEventListener("keydown", onKeyDown);
    }
    function stopListen() {
        listening.value = false;
        window.removeEventListener("keydown", onKeyDown);
    }
    function onKeyDown(e) {
        e.preventDefault();
        const backendKey = convertKeyToBackendName(e.key);
        capturedKey.value = backendKey;
        selectedKey.value = backendKey;
        stopListen();
    }

    let expandedKeys = ref([]);

    function onExpand(keys) {
        expandedKeys.value = keys;
    }
    function toggleExpand(key) {
        const index = expandedKeys.value.indexOf(key);
        if (index > -1) expandedKeys.value.splice(index, 1);
        else expandedKeys.value.push(key);
    }
    dialog.create({
        title: `修改 ${type === "key" ? "按键" : "映射值"}`,
        content: () =>
            h(NSpace, { vertical: true, style: { width: "100%" } }, [
                h("div", [
                    h(
                        NButton,
                        { onClick: startListen, disabled: listening.value, style: { marginBottom: "6px" } },
                        () => (listening.value ? "监听中..." : "开始监听按键")
                    ),
                    h(
                        "div",
                        { style: { color: "#1890ff", fontWeight: "bold" } },
                        capturedKey.value ? `监听到的按键: ${capturedKey.value}` : "未监听到按键"
                    ),
                ]),
                h(NTreeSelect, {
                    style: { width: "100%" },
                    options: treeOptions,
                    value: selectedKey.value,
                    onUpdateValue: (val) => {
                        selectedKey.value = val;
                        capturedKey.value = val;
                    },
                    multiple: false,
                    clearable: true,
                    expandedKeys: expandedKeys.value,
                    onExpand,
                    "onUpdate:expandedKeys": (keys) => (expandedKeys.value = keys),
                    onClick: (node) => {
                        if (node && !node.isLeaf) toggleExpand(node.key);
                    },
                    placeholder: "或从树中选择",
                }),
            ]),
        action: () =>
            h("div", { style: { display: "flex", justifyContent: "flex-end", gap: "8px" } }, [
                h(
                    NButton,
                    {
                        onClick: () => {
                            // 删除逻辑
                            const map = { ...data_now.value.key_map };
                            delete map[key];
                            data_now.value.key_map = map;
                            save();
                            stopListen();
                            dialog.destroyAll(); // 关闭所有弹窗
                        },
                        type: "error",
                    },
                    { default: () => "删除" }
                ),
                h(
                    NButton,
                    {
                        onClick: () => {
                            stopListen();
                            dialog.destroyAll();
                        },
                    },
                    { default: () => "取消" }
                ),
                h(
                    NButton,
                    {
                        type: "primary",
                        disabled: !selectedKey.value,
                        onClick: () => {
                            const map = { ...data_now.value.key_map };
                            if (type === "key") {
                                const oldValue = map[key];
                                delete map[key];
                                map[selectedKey.value] = oldValue;
                            } else {
                                map[key] = selectedKey.value;
                            }
                            data_now.value.key_map = map;
                            save();
                            stopListen();
                            dialog.destroyAll();
                        },
                    },
                    { default: () => "确定" }
                ),
            ]),
        onBeforeLeave: stopListen,
    });

}

// --- 新增映射 Dialog ---
function addMapping() {
    const listeningKey = ref(false);
    const listeningValue = ref(false);
    const selectedKey = ref("");
    const selectedValue = ref("");
    const capturedKey = ref("");
    const capturedValue = ref("");
    const expandedKeysAdd = ref([]);

    function startListenKey() {
        if (listeningKey.value) return;
        listeningKey.value = true;
        window.addEventListener("keydown", onKeyDownForKey);
    }
    function startListenValue() {
        if (listeningValue.value) return;
        listeningValue.value = true;
        window.addEventListener("keydown", onKeyDownForValue);
    }
    function stopListenKey() {
        listeningKey.value = false;
        window.removeEventListener("keydown", onKeyDownForKey);
    }
    function stopListenValue() {
        listeningValue.value = false;
        window.removeEventListener("keydown", onKeyDownForValue);
    }
    function onKeyDownForKey(e) {
        e.preventDefault();
        const backendKey = convertKeyToBackendName(e.key);
        capturedKey.value = backendKey;
        selectedKey.value = backendKey;
        stopListenKey();
    }
    function onKeyDownForValue(e) {
        e.preventDefault();
        const backendKey = convertKeyToBackendName(e.key);
        capturedValue.value = backendKey;
        selectedValue.value = backendKey;
        stopListenValue();
    }
    function onExpandAdd(keys) {
        expandedKeysAdd.value = keys;
    }
    function toggleExpandAdd(key) {
        const index = expandedKeysAdd.value.indexOf(key);
        if (index > -1) expandedKeysAdd.value.splice(index, 1);
        else expandedKeysAdd.value.push(key);
    }

    dialog.create({
        title: "添加新的按键映射",
        content: () =>
            h(NSpace, { vertical: true, style: { width: "100%" } }, [
                h("div", [
                    h(
                        NButton,
                        { onClick: startListenKey, disabled: listeningKey.value, style: { marginBottom: "6px" } },
                        () => (listeningKey.value ? "监听按键中..." : "开始监听按键 (Key)")
                    ),
                    h(
                        "div",
                        { style: { color: "#1890ff", fontWeight: "bold" } },
                        capturedKey.value ? `监听到的按键: ${capturedKey.value}` : "未监听到按键"
                    ),
                ]),
                h(NTreeSelect, {
                    style: { width: "100%" },
                    options: treeOptions,
                    value: selectedKey.value,
                    onUpdateValue: (val) => {
                        selectedKey.value = val;
                        capturedKey.value = val;
                    },
                    multiple: false,
                    clearable: true,
                    expandedKeys: expandedKeysAdd.value,
                    onExpand: onExpandAdd,
                    "onUpdate:expandedKeys": (keys) => (expandedKeysAdd.value = keys),
                    onClick: (node) => {
                        if (node && !node.isLeaf) toggleExpandAdd(node.key);
                    },
                    placeholder: "或从树中选择按键 (Key)",
                }),

                h("div", { style: { marginTop: "12px" } }, [
                    h(
                        NButton,
                        { onClick: startListenValue, disabled: listeningValue.value, style: { marginBottom: "6px" } },
                        () => (listeningValue.value ? "监听按键中..." : "开始监听映射值 (Value)")
                    ),
                    h(
                        "div",
                        { style: { color: "#1890ff", fontWeight: "bold" } },
                        capturedValue.value ? `监听到的按键: ${capturedValue.value}` : "未监听到按键"
                    ),
                ]),
                h(NTreeSelect, {
                    style: { width: "100%" },
                    options: treeOptions,
                    value: selectedValue.value,
                    onUpdateValue: (val) => {
                        selectedValue.value = val;
                        capturedValue.value = val;
                    },
                    multiple: false,
                    clearable: true,
                    expandedKeys: expandedKeysAdd.value,
                    onExpand: onExpandAdd,
                    "onUpdate:expandedKeys": (keys) => (expandedKeysAdd.value = keys),
                    onClick: (node) => {
                        if (node && !node.isLeaf) toggleExpandAdd(node.key);
                    },
                    placeholder: "或从树中选择映射值 (Value)",
                }),
            ]),
        positiveText: "确定",
        negativeText: "取消",
        onPositiveClick: () => {
            if (!selectedKey.value || !selectedValue.value) {
                return false;
            }
            if (!data_now.value) return false;
            const map = { ...data_now.value.key_map };
            map[selectedKey.value] = selectedValue.value;
            data_now.value.key_map = map;
            save()
            return true;

        },
        onBeforeLeave: () => {
            stopListenKey();
            stopListenValue();
        },
    });
}

// 添加新配置弹窗
function showAddConfigDialog() {
    const name = ref('');
    const windowName = ref('');

    dialog.create({
        title: '添加新配置',
        content: () =>
            h(NSpace, { vertical: true, style: { width: '100%' } }, [
                h('div', [
                    h(
                        'label',
                        { style: { fontWeight: 'bold', marginBottom: '4px' } },
                        '游戏名称'
                    ),
                    h(
                        NInput,
                        {
                            value: name.value,
                            onUpdateValue: (val) => (name.value = val),
                            placeholder: '请输入游戏名称',
                            clearable: true,
                        }
                    ),
                ]),
                h('div', [
                    h(
                        'label',
                        { style: { fontWeight: 'bold', marginBottom: '4px', marginTop: '12px' } },
                        '窗口名称'
                    ),
                    h(
                        NInput,
                        {
                            value: windowName.value,
                            onUpdateValue: (val) => (windowName.value = val),
                            placeholder: '请输入游戏窗口名称',
                            clearable: true,
                        }
                    ),
                ]),
            ]),
        positiveText: '确认添加',
        negativeText: '取消',
        onPositiveClick: () => {
            const trimmedName = name.value.trim();
            const trimmedWindow = windowName.value.trim();

            if (!trimmedName || !trimmedWindow) {
                window.$message?.warning?.('请填写完整配置名称和窗口名');
                return false;
            }

            const newId = String(
                datum.value.length
                    ? Math.max(...datum.value.map((i) => Number(i.id))) + 1
                    : 1
            );

            datum.value.push({
                id: newId,
                name: trimmedName,
                window_name: trimmedWindow,
                key_map: {},
            });

            selectedItem.value = newId;
            return true;
        },
    });
}

function save() {
    // 修正数据修改逻辑
    for (let i = 0; i < datum.value.length; i++) {
        if (datum.value[i].id === data_now.id) {
            Object.assign(datum.value[i], data_now);
            break;
        }
    }

    pywebview.api.save_config(datum.value).then(result => {
        if (result) {
            // alert("配置已保存（自动刷新）");
        } else {
            alert("保存失败");
        }
    }).catch(err => {
        alert("保存异常: " + err);
    });
}

function deleteCurrentConfig() {
    if (!data_now.value) return;

    const current = data_now.value;
    const index = datum.value.findIndex(item => item.name === current.name);

    if (index !== -1) {
        datum.value.splice(index, 1);
        data_now.value = null; // 清空当前选中项
        save();
    }
}

function toggleStrictMode() {
    exact_match.value = !exact_match.value
    localStorage.setItem("exact_match", exact_match.value)
}
</script>

<style>
.active {
    background-color: #E7F5EE !important;
}
</style>