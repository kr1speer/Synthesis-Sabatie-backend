sabatier_materials_db = [
    {
        "id": 1,
        "title": "Катализатор Ni/Al₂O₃",
        "description": "Никель на оксиде алюминия — самый распространённый катализатор метанирования. "
                       "Работает при 250–400 °C и не расходуется в реакции. Для потока газа 7 м³/ч, "
                       "дающего 1 кг метана в час, в реактор загружают около 250 г катализатора.",
        "min_reaction_value": 250,
        "molar_mass": 58.69,
        "status": "draft",
        "image_url": "http://localhost:9000/sabatie-assets/nickel_catalyst.jpeg",
        "video_url": "http://localhost:9000/sabatie-assets/nickel_catalyst.mp4",
        "liked_user_ids": list(range(1, 8))
    },
    {
        "id": 2,
        "title": "Водород H₂",
        "description": "Восстановитель в реакции Сабатье: на 1 моль метана расходуется 4 моль водорода. "
                       "Для получения 1 кг CH₄ (62,3 моль) требуется 249 моль H₂ — около 503 г. "
                       "Получается электролизом воды.",
        "min_reaction_value": 503,
        "molar_mass": 2.016,
        "status": "published",
        "image_url": "http://localhost:9000/sabatie-assets/hydrogen.jpeg",
        "video_url": "http://localhost:9000/sabatie-assets/hydrogen.mp4",
        "liked_user_ids": list(range(1, 46))
    },
    {
        "id": 3,
        "title": "Углекислый газ CO₂",
        "description": "Источник углерода для метанирования. На 1 моль метана нужен 1 моль CO₂, "
                       "поэтому для 1 кг CH₄ требуется 62,3 моль — 2744 г. "
                       "Улавливается из дымовых газов электростанций и цементных заводов.",
        "min_reaction_value": 2744,
        "molar_mass": 44.01,
        "status": "published",
        "image_url": "http://localhost:9000/sabatie-assets/carbon_dioxide.jpeg",
        "video_url": "http://localhost:9000/sabatie-assets/carbon_dioxide.mp4",
        "liked_user_ids": list(range(1, 13))
    },
    {
        "id": 4,
        "title": "Вода H₂O",
        "description": "Сырьё для получения водорода электролизом: 2H₂O → 2H₂ + O₂. Из 1 моль воды "
                       "получается 1 моль H₂, поэтому для 249 моль водорода на 1 кг метана "
                       "нужно около 4493 г воды. Используется деионизированная вода.",
        "min_reaction_value": 4493,
        "molar_mass": 18.015,
        "status": "published",
        "image_url": "http://localhost:9000/sabatie-assets/water.jpeg",
        "video_url": "http://localhost:9000/sabatie-assets/water.mp4",
        "liked_user_ids": list(range(1, 21))
    },
    {
        "id": 5,
        "title": "Биогаз CH₄ + CO₂",
        "description": "Смесь 60% метана и 40% углекислого газа со средней молярной массой 27,2 г/моль. "
                       "CO₂ из биогаза превращается в метан прямо в смеси. Чтобы получить 62,3 моль CO₂ "
                       "на 1 кг CH₄, нужно около 4244 г биогаза.",
        "min_reaction_value": 4244,
        "molar_mass": 27.23,
        "status": "published",
        "image_url": "http://localhost:9000/sabatie-assets/biogas.png",
        "video_url": "http://localhost:9000/sabatie-assets/biogas.mp4",
        "liked_user_ids": list(range(1, 4))
    }
]
