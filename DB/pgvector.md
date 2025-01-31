
我需要做个教学示例，要求如下：   
1 创建容器pgvector   
2 构建仅仅含有代谢物名称和KEGG的号数据库，数据库中只含有乳酸，丙酮酸，葡萄糖  
3 帮我查询代谢物名称丙酮（将丙酮转为embedding后进行检索）对应KEGG号是哪个最相似？  
4 修改以下内容，进行重新表述，在容器内操作   
5 以下内容经过测试时对的，帮我表述顺畅即可   


以下是在容器内操作的完整教学示例流程：

## 环境准备
**创建并启动容器**：
```bash
docker run -d --name pgvector-db \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

## 数据库操作
**进入容器内PostgreSQL命令行**：
```bash
docker exec -it pgvector-db psql -U postgres
```

**创建数据表并插入数据**：
```sql
-- 启用vector扩展
CREATE EXTENSION vector;

-- 创建代谢物表
DROP TABLE IF EXISTS metabolites;
CREATE TABLE metabolites (
    metabolite_name VARCHAR(50),
    kegg_id VARCHAR(10),
    embedding vector(3)
);

-- 插入示例数据
INSERT INTO metabolites (metabolite_name, kegg_id, embedding) VALUES
    ('葡萄糖', 'C00031', '[0.12, 0.45, 0.78]'),
    ('乳酸', 'C00186', '[0.33, 0.67, 0.91]'),
    ('丙酮酸', 'C00022', '[0.55, 0.23, 0.89]');
```

## 向量检索
**查询与丙酮最相似的代谢物**：
```sql
SELECT 
    metabolite_name,
    kegg_id,
    1 - (embedding <-> '[0.50, 0.25, 0.85]') as similarity
FROM 
    metabolites
ORDER BY 
    embedding <-> '[0.50, 0.25, 0.85]'
LIMIT 1;
```

执行上述查询后，系统会返回与丙酮向量最相似的代谢物信息，其中丙酮酸（C00022）会显示最高的相似度。

---
来自 Perplexity 的回答: pplx.ai/share
