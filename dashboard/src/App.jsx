import React, { useEffect, useRef, useState } from 'react';
import { DataSet, Network } from 'vis-network/standalone';
import { marked } from 'marked';

const API_BASE = 'http://localhost:5001/api';

function App() {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  
  // State
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [indexHtml, setIndexHtml] = useState('');
  const [policyHtml, setPolicyHtml] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [wikiHtml, setWikiHtml] = useState('');
  const [activeTab, setActiveTab] = useState('reader'); // reader, reinforce, policy
  const [rawFilename, setRawFilename] = useState('');
  const [rawContent, setRawContent] = useState('');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ nodes: 0, links: 0, lastCommit: '-' });

  // 1. 초기 데이터 로드
  useEffect(() => {
    fetchGraph();
    fetchIndex();
    fetchPolicy();
  }, []);

  const fetchGraph = async () => {
    try {
      // 1. API 서버 우선 시도
      const res = await fetch(`${API_BASE}/graph`);
      if (!res.ok) throw new Error('API server down');
      const data = await res.json();
      updateGraphState(data);
    } catch (e) {
      console.log('💡 API 서버 미감지 - 정적 폴더(/Graph.json)에서 직접 로드합니다.');
      // 2. 정적 파일 Fallback (심볼릭 링크)
      try {
        const res = await fetch('/Graph.json');
        const data = await res.json();
        updateGraphState(data);
      } catch (err) {
        console.error('그래프 로딩 최종 실패', err);
      }
    }
  };

  const updateGraphState = (data) => {
    setGraph(data);
    setStats(prev => ({
      ...prev,
      nodes: data.nodes ? data.nodes.length : 0,
      links: data.links ? data.links.length / 2 : 0
    }));
  };

  const fetchIndex = async () => {
    try {
      const res = await fetch(`${API_BASE}/index`);
      if (!res.ok) throw new Error('API server down');
      const text = await res.text();
      setIndexHtml(marked(text));
    } catch (e) {
      // 정적 Fallback
      try {
        const res = await fetch('/20_Meta/Index.md');
        const text = await res.text();
        setIndexHtml(marked(text));
      } catch (err) {
        console.error('인덱스 로딩 실패', err);
      }
    }
  };

  const fetchPolicy = async () => {
    try {
      const res = await fetch(`${API_BASE}/policy`);
      if (!res.ok) throw new Error('API server down');
      const text = await res.text();
      setPolicyHtml(marked(text));
    } catch (e) {
      // 정적 Fallback
      try {
        const res = await fetch('/20_Meta/Policy.md');
        const text = await res.text();
        setPolicyHtml(marked(text));
      } catch (err) {
        console.error('정책 로딩 실패', err);
      }
    }
  };

  // 2. vis-network 시각화 초기화
  useEffect(() => {
    if (!containerRef.current || graph.nodes.length === 0) return;

    // 카테고리별 테마 컬러 설정
    const getColor = (category) => {
      if (category.includes('Projects')) return { background: '#10b981', border: '#047857' }; // Emerald
      if (category.includes('Topics')) return { background: '#8b5cf6', border: '#6d28d9' }; // Purple
      if (category.includes('Decisions')) return { background: '#f59e0b', border: '#b45309' }; // Amber
      if (category.includes('Skills')) return { background: '#ec4899', border: '#be185d' }; // Pink
      return { background: '#6b7280', border: '#4b5563' }; // Gray
    };

    // Node 데이터 매핑
    const visNodes = new DataSet(
      graph.nodes.map(node => ({
        id: node.id,
        label: node.label,
        color: {
          ...getColor(node.category),
          highlight: { background: '#6366f1', border: '#4f46e5' },
          hover: { background: '#818cf8', border: '#6366f1' }
        },
        font: { color: '#ffffff', face: 'Outfit', size: 14 },
        shadow: true,
        shape: 'dot',
        size: node.path ? 22 : 12, // 실존 파일은 크게, 가상 노드는 작게
        title: `Category: ${node.category}\nTags: ${node.tags ? node.tags.join(', ') : 'None'}`
      }))
    );

    // Link 데이터 매핑 (중복 제거 또는 양방향 표현)
    const visEdges = new DataSet();
    const addedEdges = new Set();

    graph.links.forEach(link => {
      const edgeKey = [link.source, link.target].sort().join('-');
      if (!addedEdges.has(edgeKey)) {
        addedEdges.add(edgeKey);
        visEdges.add({
          from: link.source,
          to: link.target,
          color: { color: 'rgba(255, 255, 255, 0.15)', highlight: '#6366f1' },
          width: 1.5,
          smooth: { type: 'continuous' }
        });
      }
    });

    const data = { nodes: visNodes, edges: visEdges };
    const options = {
      interaction: {
        hover: true,
        tooltipDelay: 200,
        selectable: true
      },
      physics: {
        stabilization: true,
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04
        }
      }
    };

    const network = new Network(containerRef.current, data, options);
    networkRef.current = network;

    // 노드 클릭 핸들러
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = graph.nodes.find(n => n.id === nodeId);
        if (node) {
          handleSelectNode(node);
        }
      }
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, [graph]);

  // 3. 위키 파일 조회 및 렌더링
  const handleSelectNode = async (node) => {
    if (!node.path) {
      setSelectedNode(node);
      setWikiHtml('<div class="warning-box">⚠️ 가상 참조 노드입니다. 아직 실제 문서가 작성되지 않았습니다. 지식 강화(Reinforce)를 통해 이 주제를 다루어 보세요!</div>');
      setActiveTab('reader');
      return;
    }

    try {
      setSelectedNode(node);
      let markdown = '';
      
      try {
        const res = await fetch(`${API_BASE}/wiki/${node.path}`);
        if (!res.ok) throw new Error('API server down');
        markdown = await res.text();
      } catch (err) {
        // 정적 Fallback
        const res = await fetch(`/${node.path}`);
        if (!res.ok) throw new Error('정적 파일 로드 실패');
        markdown = await res.text();
      }
      
      const parsedHtml = parseWikiLinks(markdown);
      setWikiHtml(parsedHtml);
      setActiveTab('reader');

      // Front Matter에서 커밋 해시 등 추출
      const commitMatch = markdown.match(/github_commit:\s*"([^"]+)"/);
      if (commitMatch && commitMatch[1] !== 'pending') {
        setStats(prev => ({ ...prev, lastCommit: commitMatch[1].substring(0, 8) }));
      }
    } catch (e) {
      console.error(e);
      setWikiHtml('<div class="error-box">문서를 읽어오는 중 에러가 발생했습니다.</div>');
    }
  };

  // [[위키링크]] 파싱 함수
  const parseWikiLinks = (markdown) => {
    let cleanMd = markdown.replace(/^---[\s\S]+?---/, '');
    let html = marked(cleanMd);
    
    const regex = /\[\[(.*?)\]\]/g;
    html = html.replace(regex, (match, conceptName) => {
      const matchedNode = graph.nodes.find(n => n.label.toLowerCase() === conceptName.toLowerCase());
      if (matchedNode) {
        return `<span class="wiki-link-active" data-node-id="${matchedNode.id}">${conceptName}</span>`;
      } else {
        return `<span class="wiki-link-broken" title="존재하지 않는 지식">${conceptName}</span>`;
      }
    });

    return html;
  };

  // HTML 클릭 리스너 (쌍방향 위키링크 클릭 처리)
  const handleWikiContentClick = (e) => {
    const target = e.target;
    if (target.classList.contains('wiki-link-active')) {
      const nodeId = target.getAttribute('data-node-id');
      const node = graph.nodes.find(n => n.id === nodeId);
      if (node) {
        if (networkRef.current) {
          networkRef.current.selectNodes([nodeId]);
          networkRef.current.focus(nodeId, { scale: 1.2, animation: true });
        }
        handleSelectNode(node);
      }
    }
  };

  // 4. 지식 강화(Reinforce) 실행 버튼
  const handleReinforce = async (e) => {
    e.preventDefault();
    if (!rawFilename.trim() || !rawContent.trim()) {
      alert('파일명과 데이터 내용을 모두 입력해주세요.');
      return;
    }

    setLoading(true);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] 🚀 지식 강화 프로세스 요청 송신...`]);

    try {
      const res = await fetch(`${API_BASE}/reinforce`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: rawFilename,
          content: rawContent
        })
      });

      const result = await res.json();
      if (!res.ok) {
        throw new Error(result.error || '강화 엔진 구동 오류');
      }

      setLogs(prev => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] ✅ 저장 완료: ${result.file}`,
        `[${new Date().toLocaleTimeString()}] 🤖 엔진 출력:\n${result.output}`
      ]);
      
      setRawFilename('');
      setRawContent('');
      await fetchGraph();
      await fetchIndex();
      
      if (result.output) {
        const match = result.output.match(/완료: (.+?) ->/);
        if (match) {
          const newLabel = match[1];
          setTimeout(() => {
            fetchGraph().then(() => {
              const newNode = graph.nodes.find(n => n.label === newLabel);
              if (newNode) {
                handleSelectNode(newNode);
              }
            });
          }, 1000);
        }
      }
    } catch (err) {
      setLogs(prev => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] ❌ API 서버 에러: ${err.message}`,
        `[${new Date().toLocaleTimeString()}] 💡 [수동 지식 강화 가이드]`,
        `1. 워크스페이스 내 '00_Raw/오늘날짜/' 폴더에 파일을 저장하세요.`,
        `   파일명: ${rawFilename.endsWith('.txt') ? rawFilename : rawFilename + '.txt'}`,
        `   내용: (입력하신 본문)`,
        `2. 터미널에서 아래 명령을 수동으로 구동하세요:`,
        `   $ python3 reinforce.py`,
        `3. 완료 후 대시보드를 새로고침(F5) 하시면 지식망이 갱신됩니다.`
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Index 마크다운 리스트 클릭 시 파일 읽기 바인딩
  const handleIndexClick = (e) => {
    const target = e.target;
    if (target.tagName === 'A' && target.getAttribute('href')) {
      const href = target.getAttribute('href');
      // 상대경로 추출
      const cleanHref = href.startsWith('file://') ? href.replace(/.*위키에이전트\//, '') : href;
      const node = graph.nodes.find(n => n.path === cleanHref);
      if (node) {
        e.preventDefault();
        if (networkRef.current) {
          networkRef.current.selectNodes([node.id]);
          networkRef.current.focus(node.id, { scale: 1.2, animation: true });
        }
        handleSelectNode(node);
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', overflow: 'hidden' }}>
      {/* HEADER */}
      <header className="glass-panel" style={{ margin: '16px 24px 0 24px', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '64px', boxSizing: 'border-box' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#6366f1' }} className="pulse-glow-el" />
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '800', letterSpacing: '0.5px' }} className="gradient-text">P-Reinforce Dashboard</h1>
        </div>
        <div style={{ display: 'flex', gap: '24px', fontSize: '13px', color: '#94a3b8' }}>
          <div>🧠 지식 노드: <strong style={{ color: '#fff' }}>{stats.nodes}</strong></div>
          <div>🔗 쌍방향 링크: <strong style={{ color: '#fff' }}>{stats.links}</strong></div>
          <div>💻 동기화 커밋: <strong style={{ color: '#6366f1', fontFamily: 'monospace' }}>{stats.lastCommit}</strong></div>
        </div>
      </header>

      {/* DASHBOARD GRID */}
      <div className="dashboard-container" style={{ flex: 1, padding: '16px 24px 24px 24px', overflow: 'hidden' }}>
        
        {/* LEFT COLUMN: WIKI NAVIGATOR */}
        <aside className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '20px' }}>
          <div style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px', marginBottom: '16px' }}>
            <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: '#f1f5f9' }}>📁 Wiki Directory</h2>
            <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#64748b' }}>인덱스를 통해 분류된 문서를 탐색하세요.</p>
          </div>
          
          <div 
            className="wiki-index-list" 
            style={{ flex: 1, overflowY: 'auto', fontSize: '14px', lineHeight: '1.6' }}
            dangerouslySetInnerHTML={{ __html: indexHtml || '<p>인덱스를 로딩 중...</p>' }}
            onClick={handleIndexClick}
          />
        </aside>

        {/* CENTER COLUMN: INTERACTIVE KNOWLEDGE GRAPH */}
        <main className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
          <div style={{ position: 'absolute', top: '16px', left: '20px', zIndex: 10, pointerEvents: 'none' }}>
            <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: '#f1f5f9' }}>🕸️ Knowledge Connection Graph</h2>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px', fontSize: '11px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><i style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></i> Projects</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><i style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#8b5cf6', display: 'inline-block' }}></i> Topics</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><i style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }}></i> Decisions</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><i style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ec4899', display: 'inline-block' }}></i> Skills</span>
            </div>
          </div>
          
          {/* graph canvas */}
          <div ref={containerRef} style={{ flex: 1, width: '100%', height: '100%', outline: 'none' }} />
        </main>

        {/* RIGHT COLUMN: WORKSPACE TABS */}
        <section className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* TAB BUTTONS */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            <button 
              onClick={() => setActiveTab('reader')}
              style={{ padding: '14px', background: activeTab === 'reader' ? 'rgba(99,102,241,0.1)' : 'transparent', border: 'none', color: activeTab === 'reader' ? '#818cf8' : '#94a3b8', borderBottom: activeTab === 'reader' ? '2px solid #6366f1' : 'none', cursor: 'pointer', fontWeight: '600', fontSize: '13px' }}>
              📖 Reader
            </button>
            <button 
              onClick={() => setActiveTab('reinforce')}
              style={{ padding: '14px', background: activeTab === 'reinforce' ? 'rgba(99,102,241,0.1)' : 'transparent', border: 'none', color: activeTab === 'reinforce' ? '#818cf8' : '#94a3b8', borderBottom: activeTab === 'reinforce' ? '2px solid #6366f1' : 'none', cursor: 'pointer', fontWeight: '600', fontSize: '13px' }}>
              🚀 Reinforce
            </button>
            <button 
              onClick={() => setActiveTab('policy')}
              style={{ padding: '14px', background: activeTab === 'policy' ? 'rgba(99,102,241,0.1)' : 'transparent', border: 'none', color: activeTab === 'policy' ? '#818cf8' : '#94a3b8', borderBottom: activeTab === 'policy' ? '2px solid #6366f1' : 'none', cursor: 'pointer', fontWeight: '600', fontSize: '13px' }}>
              ⚖️ Policy
            </button>
          </div>

          {/* TAB CONTENTS */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', boxSizing: 'border-box' }}>
            
            {/* 1. WIKI READER */}
            {activeTab === 'reader' && (
              <div style={{ height: '100%' }}>
                {selectedNode ? (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px', marginBottom: '16px' }}>
                      <span style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '20px', background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.3)' }}>
                        {selectedNode.category.split('/').pop()}
                      </span>
                      <span style={{ fontSize: '11px', color: '#64748b' }}>Last reinforced: {selectedNode.updated}</span>
                    </div>
                    <div 
                      className="markdown-content"
                      onClick={handleWikiContentClick}
                      dangerouslySetInnerHTML={{ __html: wikiHtml }}
                    />
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#64748b', textAlign: 'center' }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>📖</div>
                    <p style={{ margin: 0, fontSize: '15px' }}>왼쪽 디렉토리 목록이나 지식 그래프에서<br/>원하는 노드를 클릭하여 지식을 읽어보세요.</p>
                  </div>
                )}
              </div>
            )}

            {/* 2. REINFORCE CENTER */}
            {activeTab === 'reinforce' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
                <div>
                  <h3 style={{ margin: '0 0 6px 0', fontSize: '15px', color: '#f1f5f9' }}>💡 실시간 지식 강화기</h3>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>가공되지 않은 원시 텍스트(Raw Data)를 입력하면 P-Reinforce 엔진이 가치와 연결망을 분석하여 실시간으로 위키를 고도화합니다.</p>
                </div>
                
                <form onSubmit={handleReinforce} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontSize: '12px', fontWeight: '600', color: '#94a3b8' }}>원시 파일명</label>
                    <input 
                      type="text" 
                      placeholder="예: AI_City_Plan.txt"
                      value={rawFilename}
                      onChange={(e) => setRawFilename(e.target.value)}
                      style={{ padding: '10px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)', background: '#0b0f19', color: '#fff', fontSize: '13px', outline: 'none' }}
                    />
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontSize: '12px', fontWeight: '600', color: '#94a3b8' }}>지식 내용 (Raw Data)</label>
                    <textarea 
                      rows="6"
                      placeholder="이곳에 기사 내용, 회의록, 코드 조각 등 가공되지 않은 텍스트 데이터를 입력하세요..."
                      value={rawContent}
                      onChange={(e) => setRawContent(e.target.value)}
                      style={{ padding: '10px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)', background: '#0b0f19', color: '#fff', fontSize: '13px', outline: 'none', resize: 'vertical', fontFamily: 'inherit' }}
                    />
                  </div>

                  <button 
                    type="submit"
                    disabled={loading}
                    className="gradient-bg"
                    style={{ padding: '12px', border: 'none', borderRadius: '8px', color: '#fff', fontWeight: '700', fontSize: '14px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, transition: 'opacity 0.2s' }}>
                    {loading ? '⚡ LLM 지식 구조화 및 강화 중...' : '⚡ 지식 강화(Reinforce) 실행'}
                  </button>
                </form>

                {/* LOGS PANEL */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '160px', marginTop: '8px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '600', color: '#94a3b8', marginBottom: '6px' }}>⚙️ 실행 프로세스 로그</div>
                  <div style={{ flex: 1, background: '#070a13', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', padding: '10px', fontSize: '11px', fontFamily: 'monospace', overflowY: 'auto', whiteSpace: 'pre-wrap', color: '#38bdf8' }}>
                    {logs.length === 0 ? '> 대기 중... 원시 데이터 입력을 통해 지식 엔진을 가동하세요.' : logs.join('\n')}
                  </div>
                </div>
              </div>
            )}

            {/* 3. POLICY PANEL */}
            {activeTab === 'policy' && (
              <div 
                className="policy-content" 
                dangerouslySetInnerHTML={{ __html: policyHtml || '<p>정책을 로딩 중...</p>' }}
              />
            )}

          </div>
        </section>

      </div>

      {/* Global CSS Styles (For markdown rendering) */}
      <style>{`
        .markdown-content h1, .policy-content h1 {
          font-size: 22px;
          margin-top: 0;
          color: #f1f5f9;
          font-weight: 800;
        }
        .markdown-content h2, .policy-content h2 {
          font-size: 16px;
          margin-top: 24px;
          margin-bottom: 8px;
          color: #a5b4fc;
          font-weight: 700;
          border-bottom: 1px solid rgba(255,255,255,0.05);
          padding-bottom: 6px;
        }
        .markdown-content p, .policy-content p {
          font-size: 14px;
          color: #cbd5e1;
          line-height: 1.6;
        }
        .markdown-content blockquote, .policy-content blockquote {
          margin: 16px 0;
          padding: 12px 16px;
          background: rgba(99, 102, 241, 0.08);
          border-left: 4px solid #6366f1;
          border-radius: 4px;
          color: #e2e8f0;
          font-style: italic;
        }
        .markdown-content ul, .policy-content ul {
          padding-left: 20px;
          font-size: 14px;
          color: #cbd5e1;
        }
        .markdown-content li, .policy-content li {
          margin-bottom: 8px;
        }
        .wiki-link-active {
          color: #818cf8;
          border-bottom: 1px dashed #6366f1;
          cursor: pointer;
          font-weight: 500;
          padding: 0 2px;
          transition: background 0.2s;
        }
        .wiki-link-active:hover {
          background: rgba(99, 102, 241, 0.15);
          border-radius: 4px;
        }
        .wiki-link-broken {
          color: #f43f5e;
          border-bottom: 1px dotted #e11d48;
          cursor: help;
        }
        .warning-box {
          background: rgba(245, 158, 11, 0.08);
          border: 1px solid rgba(245, 158, 11, 0.2);
          border-radius: 8px;
          padding: 16px;
          color: #f59e0b;
          font-size: 13px;
        }
        .error-box {
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: 8px;
          padding: 16px;
          color: #ef4444;
          font-size: 13px;
        }
        
        /* Wiki Directory index customization */
        .wiki-index-list h2 {
          font-size: 14px;
          color: #94a3b8;
          margin-top: 18px;
          margin-bottom: 6px;
          font-weight: 700;
        }
        .wiki-index-list p {
          font-size: 11px;
          color: #475569;
          margin: 0 0 8px 0;
          font-style: italic;
        }
        .wiki-index-list ul {
          list-style: none;
          padding-left: 0;
          margin: 0;
        }
        .wiki-index-list li {
          margin-bottom: 6px;
          padding-left: 8px;
          border-left: 2px solid rgba(255,255,255,0.05);
        }
        .wiki-index-list a {
          color: #e2e8f0;
          text-decoration: none;
          transition: color 0.2s;
        }
        .wiki-index-list a:hover {
          color: #818cf8;
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
}

export default App;
