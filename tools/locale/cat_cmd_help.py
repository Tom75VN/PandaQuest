# -*- coding: utf-8 -*-
# /pq help and the generic command chrome. key -> (en, fr, ru, cn)

STRINGS = {

"CMD_HELP_TITLE": (
    "v%s commands:", "v%s commandes :", "v%s команды:", "v%s 命令："),

"CMD_HELP_CONFIG": (
    "/pq config    open the options window",
    "/pq config    ouvrir la fenêtre d'options",
    "/pq config    открыть окно настроек",
    "/pq config    打开选项窗口",
),
"CMD_HELP_CONFIG_BUTTON": (
    "/pq config button on|off      the settings button beside the minimap",
    "/pq config button on|off      le bouton de réglages à côté de la mini-carte",
    "/pq config button on|off      кнопка настроек рядом с миникартой",
    "/pq config button on|off      小地图旁的设置按钮",
),
"CMD_HELP_STATUS": (
    "/pq status    what this build established about the client",
    "/pq status    ce que cette version a établi sur le client",
    "/pq status    что эта сборка установила о клиенте",
    "/pq status    此版本对客户端的确认结果",
),
"CMD_HELP_QUESTS": (
    "/pq quests    the current quest log model",
    "/pq quests    le modèle actuel du journal de quêtes",
    "/pq quests    текущая модель журнала заданий",
    "/pq quests    当前任务日志模型",
),
"CMD_HELP_EVENTS": (
    "/pq events    which quest events this client accepted and fired",
    "/pq events    quels événements de quête ce client a acceptés et déclenchés",
    "/pq events    какие события заданий клиент принял и вызвал",
    "/pq events    此客户端接受并触发了哪些任务事件",
),
"CMD_HELP_MAP": (
    "/pq map       current map identity and world-map pin status",
    "/pq map       identité de la carte actuelle et état des repères",
    "/pq map       текущая карта и состояние меток на карте мира",
    "/pq map       当前地图标识与世界地图标记状态",
),
"CMD_HELP_MAP_STYLE": (
    "/pq map dots|areas|both  draw quest objectives as dots, shaded areas or both",
    "/pq map dots|areas|both  dessiner les objectifs en points, en zones ombrées ou les deux",
    "/pq map dots|areas|both  рисовать цели точками, областями или и тем и другим",
    "/pq map dots|areas|both  以圆点、阴影区域或两者绘制任务目标",
),
"CMD_HELP_MAP_VENDORS": (
    "/pq map vendors on|off  show where quest items you have to buy are sold",
    "/pq map vendors on|off  montrer où s'achètent les objets de quête à acheter",
    "/pq map vendors on|off  показывать, где продаются предметы заданий",
    "/pq map vendors on|off  显示需要购买的任务物品在何处出售",
),
"CMD_HELP_MINIMAP": (
    "/pq minimap   quest pins around the player on the minimap",
    "/pq minimap   repères de quête autour du joueur sur la mini-carte",
    "/pq minimap   метки заданий вокруг игрока на миникарте",
    "/pq minimap   小地图上玩家周围的任务标记",
),
"CMD_HELP_MINIMAP_ONOFF": (
    "/pq minimap on|off            draw them, or stop",
    "/pq minimap on|off            les dessiner, ou arrêter",
    "/pq minimap on|off            рисовать их или прекратить",
    "/pq minimap on|off            绘制或停止绘制",
),
"CMD_HELP_MINIMAP_SPAN": (
    "/pq minimap span <yards>       dial in the scale for this zoom step",
    "/pq minimap span <yards>       ajuster l'échelle pour ce niveau de zoom",
    "/pq minimap span <yards>       подстроить масштаб для этого шага зума",
    "/pq minimap span <yards>       为该缩放级别微调比例",
),
"CMD_HELP_MINIMAP_INDOORS": (
    "/pq minimap indoors on|off    withhold markers indoors, or draw them anyway",
    "/pq minimap indoors on|off    masquer les repères en intérieur, ou les dessiner quand même",
    "/pq minimap indoors on|off    скрывать метки в помещении или рисовать их всё равно",
    "/pq minimap indoors on|off    在室内隐藏标记，或仍然绘制",
),
"CMD_HELP_DB": (
    "/pq db        static quest database state",
    "/pq db        état de la base de données de quêtes",
    "/pq db        состояние статической базы заданий",
    "/pq db        静态任务数据库状态",
),
"CMD_HELP_TOOLTIP": (
    "/pq tooltip   entity-tooltip objective diagnostics",
    "/pq tooltip   diagnostics des objectifs dans les infobulles",
    "/pq tooltip   диагностика целей в подсказках существ",
    "/pq tooltip   实体提示中的目标诊断",
),
"CMD_HELP_TOOLTIP_DELAY": (
    "/pq tooltip delay <seconds>   set cursor-follow fade hold",
    "/pq tooltip delay <secondes>  regler le delai de suivi du curseur",
    "/pq tooltip delay <секунды>   задержка подсказки у курсора",
    "/pq tooltip delay <秒>        设置跟随光标提示的停留时间",
),
"CMD_HELP_TRACKER": (
    "/pq tracker   the movable quest tracker window",
    "/pq tracker   la fenêtre de suivi de quêtes déplaçable",
    "/pq tracker   перемещаемое окно трекера заданий",
    "/pq tracker   可移动的任务追踪窗口",
),
"CMD_HELP_TRACKER_ONOFF": (
    "/pq tracker on|off|toggle     show or hide it",
    "/pq tracker on|off|toggle     l'afficher ou la masquer",
    "/pq tracker on|off|toggle     показать или скрыть его",
    "/pq tracker on|off|toggle     显示或隐藏",
),
"CMD_HELP_TRACKER_RESET": (
    "/pq tracker reset             move it back to its default position",
    "/pq tracker reset             la remettre à sa position par défaut",
    "/pq tracker reset             вернуть его в положение по умолчанию",
    "/pq tracker reset             移回默认位置",
),
"CMD_HELP_TRACKER_OBJECTIVES": (
    "/pq tracker objectives all|tracked|none",
    "/pq tracker objectives all|tracked|none",
    "/pq tracker objectives all|tracked|none",
    "/pq tracker objectives all|tracked|none",
),
"CMD_HELP_TRACKER_ZONES": (
    "/pq tracker zones             group by zone, or do not",
    "/pq tracker zones             grouper par zone, ou non",
    "/pq tracker zones             группировать по зонам или нет",
    "/pq tracker zones             按区域分组，或不分组",
),
"CMD_HELP_TRACKER_RECENT": (
    "/pq tracker recent            lift the quest that just advanced, or do not",
    "/pq tracker recent            remonter la quête qui vient d'avancer, ou non",
    "/pq tracker recent            поднимать задание с новым прогрессом, или нет",
    "/pq tracker recent            是否将刚有进展的任务置顶",
),
"CMD_HELP_TRACKER_WIDTH": (
    "/pq tracker width <110-600>   how wide the window is",
    "/pq tracker width <110-600>   largeur de la fenêtre",
    "/pq tracker width <110-600>   ширина окна",
    "/pq tracker width <110-600>   窗口宽度",
),
"CMD_HELP_TRACKER_HEIGHT": (
    "/pq tracker height <60-900>   max height in pixels, 0 for no limit",
    "/pq tracker height <60-900>   hauteur max en pixels, 0 pour aucune limite",
    "/pq tracker height <60-900>   макс. высота в пикселях, 0 -- без ограничения",
    "/pq tracker height <60-900>   最大高度（像素），0 表示不限",
),
"CMD_HELP_TRACKER_UNFOLD": (
    "/pq tracker unfold            reopen every folded quest and zone",
    "/pq tracker unfold            rouvrir toutes les quêtes et zones repliées",
    "/pq tracker unfold            раскрыть все свёрнутые задания и зоны",
    "/pq tracker unfold            展开所有折叠的任务和区域",
),
"CMD_HELP_TRACKER_UNHIDEALL": (
    "/pq tracker unhideall         bring back every quest untracked out of the tracker",
    "/pq tracker unhideall         ramener toutes les quêtes retirées du suivi",
    "/pq tracker unhideall         вернуть все задания, убранные из трекера",
    "/pq tracker unhideall         恢复所有被移出追踪器的任务",
),
"CMD_HELP_TRACKER_NATIVE": (
    "/pq tracker native            hide or restore the client's own watch panel",
    "/pq tracker native            masquer ou restaurer le panneau de suivi du client",
    "/pq tracker native            скрыть или вернуть родную панель слежения клиента",
    "/pq tracker native            隐藏或恢复客户端自带的追踪面板",
),

"CMD_HELP_MAIN_SET": (
    "/pq main <index or title>     follow a quest with the HUD waypoint",
    "/pq main <index ou titre>     suivre une quête avec le repère ATH",
    "/pq main <индекс или название>  следовать за заданием с маркером HUD",
    "/pq main <序号或标题>          用 HUD 路径点跟随一个任务",
),
"CMD_HELP_MAIN_REPORT": (
    "/pq main                      report the followed quest",
    "/pq main                      indiquer la quête suivie",
    "/pq main                      сообщить, за каким заданием следуем",
    "/pq main                      报告当前跟随的任务",
),
"CMD_HELP_MAIN_CLEAR": (
    "/pq main clear                follow nearest node",
    "/pq main clear                suivre le noeud le plus proche",
    "/pq main clear                следовать к ближайшей точке",
    "/pq main clear                跟随最近节点",
),
"CMD_HELP_NAV": (
    "/pq nav       quest navigator diagnostics",
    "/pq nav       diagnostics du navigateur de quete",
    "/pq nav       диагностика навигатора заданий",
    "/pq nav       任务导航诊断"),
"CMD_HELP_MOBNAV": (
    "/pq mobnav    tracked mob navigator diagnostics",
    "/pq mobnav    diagnostics du navigateur de creature",
    "/pq mobnav    диагностика навигатора существ",
    "/pq mobnav    生物导航诊断"),
"CMD_HELP_MAIN_DISABLED": (
    "/pq main, /pq waypoint   disabled in this build",
    "/pq main, /pq waypoint   désactivés dans cette version",
    "/pq main, /pq waypoint   отключены в этой сборке",
    "/pq main, /pq waypoint   在此版本中已停用",
),

"CMD_HELP_TRACK": (
    "/pq track <index or title>    track a quest",
    "/pq track <index ou titre>    suivre une quête",
    "/pq track <индекс или название>  отслеживать задание",
    "/pq track <序号或标题>         追踪一个任务",
),
"CMD_HELP_UNTRACK": (
    "/pq untrack <index or title>  stop tracking a quest",
    "/pq untrack <index ou titre>  ne plus suivre une quête",
    "/pq untrack <индекс или название>  прекратить отслеживание",
    "/pq untrack <序号或标题>       停止追踪一个任务",
),
"CMD_HELP_TOGGLE": (
    "/pq toggle <index or title>   toggle quest tracking",
    "/pq toggle <index ou titre>   basculer le suivi d'une quête",
    "/pq toggle <индекс или название>  переключить отслеживание",
    "/pq toggle <序号或标题>        切换任务追踪",
),
"CMD_HELP_HIDE": (
    "/pq hide <index or title>     hide a quest's pins from the world map",
    "/pq hide <index ou titre>     masquer les repères d'une quête sur la carte",
    "/pq hide <индекс или название>  скрыть метки задания с карты мира",
    "/pq hide <序号或标题>          在世界地图上隐藏某任务的标记",
),
"CMD_HELP_UNHIDE": (
    "/pq unhide <index or title>   restore a quest's map pins",
    "/pq unhide <index ou titre>   restaurer les repères d'une quête",
    "/pq unhide <индекс или название>  вернуть метки задания на карту",
    "/pq unhide <序号或标题>        恢复某任务的地图标记",
),
"CMD_HELP_HIDDEN": (
    "/pq hidden                    list quests hidden from the map",
    "/pq hidden                    lister les quêtes masquées de la carte",
    "/pq hidden                    список заданий, скрытых с карты",
    "/pq hidden                    列出从地图隐藏的任务",
),
"CMD_HELP_RESETMARKED": (
    "/pq resetmarked               undo every shift/Ctrl-click 'mark done' on the map",
    "/pq resetmarked               annuler chaque « terminée » posée par Maj/Ctrl+clic",
    "/pq resetmarked               отменить все отметки «выполнено» по Shift/Ctrl+клику",
    "/pq resetmarked               撤销地图上所有 Shift/Ctrl+点击的“已完成”标记",
),
"CMD_HELP_RESETMARKED_ALL": (
    "/pq resetmarked all           also undo marks made before that tracking existed",
    "/pq resetmarked all           annuler aussi les marques posées avant ce suivi",
    "/pq resetmarked all           отменить и отметки, сделанные до появления учёта",
    "/pq resetmarked all           同时撤销该记录功能出现前所做的标记",
),
"CMD_HELP_PFQUEST": (
    "/pq pfquest                   report what pfQuest's saved history holds",
    "/pq pfquest                   indiquer ce que contient l'historique de pfQuest",
    "/pq pfquest                   сообщить, что содержит история pfQuest",
    "/pq pfquest                   报告 pfQuest 的历史记录内容",
),
"CMD_HELP_PFQUEST_IMPORT": (
    "/pq pfquest import            import it -- enables pfQuest for one reload if needed",
    "/pq pfquest import            l'importer -- active pfQuest pour un rechargement si besoin",
    "/pq pfquest import            импортировать -- при необходимости включит pfQuest на одну перезагрузку",
    "/pq pfquest import            导入 -- 必要时为一次重载启用 pfQuest",
),
"CMD_HELP_PFQUEST_UNDO": (
    "/pq pfquest undo              take back everything a previous import added",
    "/pq pfquest undo              annuler tout ce qu'un import précédent a ajouté",
    "/pq pfquest undo              отменить всё, что добавил предыдущий импорт",
    "/pq pfquest undo              撤回之前导入所添加的一切",
),
"CMD_HELP_ANNOUNCE": (
    u"/pq announce  objective progress reported in party chat",
    u"/pq announce  progression des objectifs annoncée en chat de groupe",
    u"/pq announce  прогресс целей в чате группы",
    u"/pq announce  在小队频道播报目标进度",
),
"CMD_HELP_ANNOUNCE_ONOFF": (
    u"/pq announce on|off           turn the party-chat report on or off",
    u"/pq announce on|off           activer ou désactiver l'annonce en groupe",
    u"/pq announce on|off           включить или выключить отчёт в чат группы",
    u"/pq announce on|off           开启或关闭小队频道播报",
),
"CMD_HELP_GEAR": (
    "/pq gear                  how the open turn-in window's rewards were ranked",
    "/pq gear                  comment les recompenses de la fenetre de rendu ont ete classees",
    "/pq gear                  как оценены награды в открытом окне сдачи задания",
    "/pq gear                  当前交任务窗口中奖励的评估方式",
),
"CMD_HELP_MARKS": (
    "/pq marks                 quest marks over creatures in the world",
    "/pq marks                 marques de quête sur les créatures du monde",
    "/pq marks                 метки заданий над существами в мире",
    "/pq marks                 世界中生物头顶的任务标记",
),
"CMD_HELP_MARKS_ONOFF": (
    "/pq marks on|off          mark quest creatures with a raid target icon",
    "/pq marks on|off          marquer les créatures de quête avec une icône de raid",
    "/pq marks on|off          помечать существ заданий рейдовой меткой",
    "/pq marks on|off          用团队目标图标标记任务生物",
),
"CMD_HELP_MARKS_ICON": (
    "/pq marks icon <1-8>      which mark: 1 star .. 8 skull",
    "/pq marks icon <1-8>      quelle marque : 1 étoile .. 8 crâne",
    "/pq marks icon <1-8>      какая метка: 1 звезда .. 8 череп",
    "/pq marks icon <1-8>      使用哪种标记：1 星星 .. 8 骷髅",
),
"CMD_HELP_MARKS_GROUP": (
    "/pq marks group on|off    also mark while in a party or raid",
    "/pq marks group on|off    marquer aussi en groupe ou en raid",
    "/pq marks group on|off    помечать также в группе или рейде",
    "/pq marks group on|off    在小队或团队中也进行标记",
),
"CMD_HELP_WORLDSCAN": (
    "/pq worldscan             inventory WorldFrame's children (nameplate hunt)",
    "/pq worldscan             inventorier les enfants de WorldFrame (chasse aux barres de nom)",
    "/pq worldscan             перечислить дочерние объекты WorldFrame (поиск индикаторов)",
    "/pq worldscan             清点 WorldFrame 的子对象（查找姓名板）",
),
"CMD_HELP_WORLDSCAN_CHILD": (
    "/pq worldscan <n>         one child in full: every region and child",
    "/pq worldscan <n>         un enfant en détail : chaque région et enfant",
    "/pq worldscan <n>         один дочерний объект целиком: все области и дети",
    "/pq worldscan <n>         完整显示某个子对象：所有区域与子级",
),
"CMD_HELP_DEBUG": (
    "/pq debug     toggle debug output",
    "/pq debug     activer/désactiver la sortie de débogage",
    "/pq debug     включить/выключить отладочный вывод",
    "/pq debug     切换调试输出",
),

# --- generic command chrome --------------------------------------------------
"CMD_UNKNOWN": (
    "unknown command: %s", "commande inconnue : %s",
    "неизвестная команда: %s", "未知命令：%s"),
"CMD_DEBUG_ENABLED": (
    "debug output enabled", "sortie de débogage activée",
    "отладочный вывод включён", "调试输出已启用"),
"CMD_DEBUG_DISABLED": (
    "debug output disabled", "sortie de débogage désactivée",
    "отладочный вывод отключён", "调试输出已禁用"),
"CMD_STATE_DISABLED": ("disabled", "désactivé", "отключено", "已停用"),

"CMD_MODULE_MISSING_QUEST_STATE": (
    "quest state module is not loaded",
    "le module d'état des quêtes n'est pas chargé",
    "модуль состояния заданий не загружен",
    "任务状态模块未加载",
),
"CMD_MODULE_MISSING_EVENTS": (
    "event module is not loaded", "le module d'événements n'est pas chargé",
    "модуль событий не загружен", "事件模块未加载"),
"CMD_MODULE_MISSING_MAP": (
    "map module is not loaded", "le module de carte n'est pas chargé",
    "модуль карты не загружен", "地图模块未加载"),
"CMD_MODULE_MISSING_CONFIG": (
    "config module is not loaded", "le module de configuration n'est pas chargé",
    "модуль настроек не загружен", "配置模块未加载"),
"CMD_MODULE_MISSING_MINIMAP": (
    "minimap pin module is not loaded",
    "le module de repères de mini-carte n'est pas chargé",
    "модуль меток миникарты не загружен", "小地图标记模块未加载"),
"CMD_MODULE_MISSING_DATABASE": (
    "database module is not loaded", "le module de base de données n'est pas chargé",
    "модуль базы данных не загружен", "数据库模块未加载"),
"CMD_MODULE_MISSING_TOOLTIP": (
    "entity tooltip module is not loaded",
    "le module d'infobulle d'entité n'est pas chargé",
    "модуль подсказок существ не загружен", "实体提示模块未加载"),
"CMD_MODULE_MISSING_MARKS": (
    "quest mark module is not loaded",
    "le module de marques de quête n'est pas chargé",
    "модуль меток заданий не загружен", "任务标记模块未加载"),
"CMD_MODULE_MISSING_WORLDSCAN": (
    "world scan module is not loaded", "le module d'analyse du monde n'est pas chargé",
    "модуль сканирования мира не загружен", "世界扫描模块未加载"),
"CMD_MODULE_MISSING_TRACKER": (
    "tracker module is not loaded", "le module de suivi n'est pas chargé",
    "модуль отслеживания не загружен", "追踪模块未加载"),
"CMD_MODULE_MISSING_TRACKER_FRAME": (
    "the tracker module is not loaded", "le module de la fenêtre de suivi n'est pas chargé",
    "модуль окна трекера не загружен", "追踪器模块未加载"),
"CMD_MODULE_MISSING_REQUIRED": (
    "required modules are not loaded", "les modules requis ne sont pas chargés",
    "необходимые модули не загружены", "所需模块未加载"),
"CMD_MODULE_MISSING_HISTORY": (
    "quest history module is not loaded",
    "le module d'historique des quêtes n'est pas chargé",
    "модуль истории заданий не загружен", "任务历史模块未加载"),
"CMD_MODULE_MISSING_PFQUEST": (
    "the pfQuest import module is not loaded",
    "le module d'import pfQuest n'est pas chargé",
    "модуль импорта pfQuest не загружен", "pfQuest 导入模块未加载"),
"CMD_MODULE_MISSING_MAINQUEST": (
    "the main quest module is unavailable",
    "le module de quête principale est indisponible",
    "модуль главного задания недоступен", "主线任务模块不可用"),
"CMD_MODULE_MISSING_WAYPOINT": (
    "the waypoint module is unavailable", "le module de repère est indisponible",
    "модуль маркера недоступен", "路径点模块不可用"),
"CMD_MODULE_MISSING_SETTINGS": (
    "the settings module is not loaded", "le module de réglages n'est pas chargé",
    "модуль настроек не загружен", "设置模块未加载"),

"CMD_HELP_RARE": (
    u"/pq rare      the rare / elite proximity alert",
    u"/pq rare      l'alerte de proximité rare / élite",
    u"/pq rare      оповещение о редких и элитных",
    u"/pq rare      稀有 / 精英接近提醒",
),
"CMD_HELP_RARE_ONOFF": (
    u"/pq rare on|off               turn the alert on or off",
    u"/pq rare on|off               activer ou désactiver l'alerte",
    u"/pq rare on|off               включить или выключить оповещение",
    u"/pq rare on|off               开启或关闭提醒",
),
"CMD_HELP_RARE_RANGE": (
    u"/pq rare range <yards>        how near counts as near",
    u"/pq rare range <mètres>       à quelle distance l'alerte se déclenche",
    u"/pq rare range <метры>        на каком расстоянии срабатывать",
    u"/pq rare range <码>          多近算靠近",
),
"CMD_HELP_RARE_SOUND": (
    u"/pq rare sound <kit>          play and keep a SoundEntries kit",
    u"/pq rare sound <kit>          jouer et garder un kit SoundEntries",
    u"/pq rare sound <kit>          проиграть и сохранить набор SoundEntries",
    u"/pq rare sound <kit>          试听并保存 SoundEntries 音效",
),
"CMD_HELP_RARE_RESET": (
    u"/pq rare reset                put the card back where it started",
    u"/pq rare reset                remettre la carte a sa place d'origine",
    u"/pq rare reset                вернуть карточку на исходное место",
    u"/pq rare reset                将卡片放回初始位置",
),
"CMD_HELP_RARE_TEST": (
    u"/pq rare test                 raise the card on the nearest one",
    u"/pq rare test                 afficher la carte pour le plus proche",
    u"/pq rare test                 показать карточку для ближайшего",
    u"/pq rare test                 对最近的目标弹出提示",
),
}
