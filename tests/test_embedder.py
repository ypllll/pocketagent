import pytest

from pocket_agent.documents.embedder import Embedder
from pocket_agent.documents.SiliconFlowEmbedder import siliconflowembedder


@pytest.fixture(scope="module")
def embedder():
    """整个文件只构造一次，减少重复开销"""
    return siliconflowembedder.from_env()


def test_抽象类不能直接实例化():
    with pytest.raises(TypeError):
        Embedder()


def test_空输入不发请求(embedder):
    assert embedder.embed([]) == []


def test_单条文本返回一条固定维度的向量(embedder):
    result = embedder.embed(["iPhoneDuo 的退货政策是什么"])
    assert len(result) == 1
    assert len(result[0]) == embedder.dimensions
    assert all(isinstance(x, (int, float)) for x in result[0])


def test_同一个文本两次结果完全一致(embedder):
    a = embedder.embed(["退货"])
    b = embedder.embed(["退货"])
    assert a == b


def test_批量的条数与顺序都和输入对应(embedder):
    texts = ["退货政策", "产品价格", "保修范围"]
    result = embedder.embed(texts)
    assert len(result) == 3

    # 批量里的第 2 条，应该和"单独只调第 2 条"的结果完全一样
    single = embedder.embed([texts[1]])
    assert result[1] == single[0]