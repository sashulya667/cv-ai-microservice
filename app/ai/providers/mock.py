import json

from app.ai.base import LLMClient, LLMInput, LLMResponse


class MockClient(LLMClient):
    async def generate(self, *, inp: LLMInput) -> LLMResponse:
        payload = {
            "match_score": 72,
            "ats_match_score": 68,
            "seniority_fit": "aligned",
            "overall_fit": "good",
            "summary": (
                "Кандидат демонстрирует хорошее соответствие вакансии с опытом работы в релевантной области. "
                "Seniority fit: aligned — уровень задач соответствует требованиям Middle-Senior позиции. "
                "Сильные стороны: опыт с требуемым стеком технологий, работа в продуктовых командах. "
                "Критичные пробелы: отсутствие измеримых метрик в достижениях, недостаточно evidence лидерства. "
                "Главная рекомендация: переписать все достижения по формуле X-Y-Z с конкретными цифрами."
            ),
            "matching_strengths": [
                "Python backend 5+ лет → подтверждено: 3 года в продуктовой компании + 2 года фриланс",
                "Опыт с REST API → подтверждено: разработка микросервисной архитектуры для e-commerce",
                "PostgreSQL и оптимизация запросов → подтверждено: работа с базами данных на проектах",
            ],
            "gaps": [
                "[MUST-HAVE] Нет примеров работы с Kubernetes и Docker в production",
                "[MUST-HAVE CONTEXT] Отсутствует опыт в high-load системах (>100K RPS)",
                "[SENIORITY GAP] Недостаточно evidence архитектурных решений на уровне Senior",
                "[NICE-TO-HAVE] Отсутствует опыт с GraphQL",
            ],
            "recommendations": [
                "Переписать достижения по формуле X-Y-Z: 'Снизил latency API на 40% (с 200ms до 120ms) через внедрение кэширования Redis'",
                "Добавить конкретные метрики: размер команды, объем пользователей, throughput систем",
                "Усилить evidence лидерства: добавить примеры менторинга, code review, архитектурных решений",
                "Показать масштаб задач: указать нагрузку систем (RPS, DAU, объем данных)",
                "Добавить keywords: Kubernetes, Docker, CI/CD, microservices",
            ],
            "matching_keywords": [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "REST API",
                "Git",
                "Agile",
            ],
            "missing_keywords": [
                "Kubernetes [!]",
                "Docker [!]",
                "Redis",
                "Celery",
                "GraphQL",
                "AWS",
            ],
            "impact_analysis": {
                "achievements_quality": "moderate",
                "measurability_score": 35,
                "xyz_formula_usage": 20,
                "leadership_evidence": [
                    "Code review практика → упоминается, но без деталей масштаба",
                    "Менторинг junior разработчиков → упомянуто вскользь, нет конкретики",
                ],
                "individual_impact": [
                    "Оптимизация запросов → есть упоминание, но нет метрик (насколько быстрее)",
                    "Разработка API → нет информации о нагрузке или влиянии на бизнес",
                ],
                "red_flags": [
                    "Большинство достижений без метрик (только 35% имеют цифры)",
                    "Формулировки 'участвовал в проекте' без указания личного вклада",
                    "Описание обязанностей вместо результатов в разделе Experience",
                ],
            },
            "context_analysis": {
                "company_scale_match": "partial",
                "task_scale_match": "partial",
                "autonomy_level": "designer",
                "complexity_match": (
                    "Опыт в SMB компаниях с умеренной нагрузкой. "
                    "Вакансия требует работу с high-load системами и микросервисной архитектурой в production. "
                    "Есть gap в масштабе задач, но базовые навыки присутствуют."
                ),
                "environment_fit": (
                    "Опыт в продуктовых компаниях соответствует требованиям вакансии. "
                    "Переход из SMB в более крупную компанию потребует адаптации к большим объемам и сложности инфраструктуры."
                ),
            },
            "section_feedback": {
                "Experience": (
                    "Текущий контент показывает релевантный опыт, но большинство буллетов описывают обязанности, а не результаты. "
                    "Критичные правки: (1) Переписать каждый буллет по формуле X-Y-Z с метриками, "
                    "(2) Добавить масштаб задач (размер команды, нагрузка системы), "
                    "(3) Показать личный вклад через конкретные цифры. "
                    "Приоритет: критично для повышения match_score."
                ),
                "Skills": (
                    "Хороший набор технологий, но отсутствуют ключевые требования вакансии (Kubernetes, Docker). "
                    "Правки: (1) Добавить containerization технологии, (2) Группировать по категориям (Backend, Databases, DevOps), "
                    "(3) Удалить устаревшие или нерелевантные навыки. "
                    "Приоритет: важно для ATS matching."
                ),
            },
        }

        return LLMResponse(
            text=json.dumps(payload, ensure_ascii=False),
            raw={"mock": True},
        )
