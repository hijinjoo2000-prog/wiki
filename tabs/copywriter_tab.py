# -*- coding: utf-8 -*-
import sys
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                               QPushButton, QTextEdit, QGroupBox, QTabWidget, QSplitter, QTextBrowser, QMessageBox, QApplication)
from PySide6.QtCore import Qt

# Local imports
from agents.workers import AgentPipelineWorker
from utils.local_llm_manager import on_local_ai_test_clicked

class CopywriterTabMixin:
    def setup_tab_copywriter(self):
        layout = QVBoxLayout(self.tab_copywriter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea = self.create_copywriter_scroll_area()
        layout.addWidget(scroll)

    def create_copywriter_scroll_area(self):
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        gb = QGroupBox("✍️ 서프로 AI 콘텐츠 기획 및 초안 작성")
        v = QVBoxLayout(gb)
        
        ctrl_grid = QGridLayout()
        
        self.btn_write_blog_normal = QPushButton("✍️ 블로그 일반 초안 작성")
        self.btn_write_blog_normal.setStyleSheet("background-color: #5f27cd; font-size: 13px; height: 50px; font-weight: bold;")
        self.btn_write_blog_normal.clicked.connect(lambda: self.on_write_start("blog", draft_type="normal"))
        ctrl_grid.addWidget(self.btn_write_blog_normal, 0, 0)

        self.btn_write_blog_seo = QPushButton("🎯 블로그 SEO 최적화 초안")
        self.btn_write_blog_seo.setStyleSheet("background-color: #2e86de; font-size: 13px; height: 50px; font-weight: bold;")
        self.btn_write_blog_seo.clicked.connect(lambda: self.on_write_start("blog", draft_type="seo"))
        ctrl_grid.addWidget(self.btn_write_blog_seo, 0, 1)

        self.btn_write_cafe_normal = QPushButton("☕ 카페 일반 초안 작성")
        self.btn_write_cafe_normal.setStyleSheet("background-color: #d35400; font-size: 13px; height: 50px; font-weight: bold;")
        self.btn_write_cafe_normal.clicked.connect(lambda: self.on_write_start("cafe", draft_type="normal"))
        ctrl_grid.addWidget(self.btn_write_cafe_normal, 1, 0)

        self.btn_write_cafe_seo = QPushButton("🔥 카페 SEO 최적화 초안")
        self.btn_write_cafe_seo.setStyleSheet("background-color: #e74c3c; font-size: 13px; height: 50px; font-weight: bold;")
        self.btn_write_cafe_seo.clicked.connect(lambda: self.on_write_start("cafe", draft_type="seo"))
        ctrl_grid.addWidget(self.btn_write_cafe_seo, 1, 1)

        self.btn_local_ai_test = QPushButton("🤖 로컬 AI 연결 테스트")
        self.btn_local_ai_test.setStyleSheet("background-color: #2c3e50; font-size: 13px; height: 105px; font-weight: bold;")
        self.btn_local_ai_test.clicked.connect(self.on_local_ai_test)
        ctrl_grid.addWidget(self.btn_local_ai_test, 0, 2, 2, 1)

        v.addLayout(ctrl_grid)
        
        self.console_copywriter = QTextEdit()
        self.console_copywriter.setReadOnly(True)
        self.console_copywriter.setPlaceholderText("여기에 AI 에이전트 기획 협업 로그가 실시간 출력됩니다...")
        self.console_copywriter.setStyleSheet("background-color: #2f3542; font-family: Consolas; font-size: 12px; height: 120px;")
        v.addWidget(self.console_copywriter)
        
        h_workspace = QHBoxLayout()
        
        gb_rules = QGroupBox("📋 적용 규칙 및 팩트 체크리스트")
        gb_rules.setFixedWidth(280)
        v_rules = QVBoxLayout(gb_rules)
        v_rules.setContentsMargins(10, 15, 10, 10)
        
        rules_text = [
            ("✓ 동작구 규제 팩트 반영", "투기과열지구, 토지거래허가구역, 5년재당첨제한 등 규제 경고 및 도시정비법 제39조 법령 100% 인용"),
            ("✓ 실거래가 3요소 상세화", "34평형(전용 84㎡) 대장 아파트(아크로리버하임 등) 최근 1년 내 실거래 연월, 평형, 가격 구체적 인용"),
            ("✓ 안전마진 분석 고도화", "예상 시세 대조 안전마진 계산 및 볼드체 표기 (예: **8.5억**)"),
            ("✓ 추가분담금 선명시", "추가분담금 총액 선제 명시 및 납부 구조(10:0:90) 명시 후 일정표 작성"),
            ("✓ 금지 단어/주체 표현 제거", "'자금조달모델', '실거래가 밴드', '사업시행 조합은~' 단어 원천 차단"),
            ("✓ 표준 권장 표현 적용", "'조합사무실', '조합전화번호' 대체 및 포스코 브랜드 '오띠에르' 오타 교정"),
            ("✓ 입지 분석 후속 배치", "여의도/강남 접근성 등 입지 분석을 실전 주의사항 다음, 명함/배너 직전 배치 (본문 내 CTA 일절 금지)"),
            ("✓ 9대 이미지 순서 준수", "[IMAGE_1]~[IMAGE_9] 자리표시자 레이아웃 순서 엄격 고정")
        ]
        
        for title, desc in rules_text:
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("font-weight: bold; color: #10ac84; font-size: 11px; margin-top: 3px;")
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #a4b0be; font-size: 10px; margin-bottom: 3px;")
            v_rules.addWidget(lbl_title)
            v_rules.addWidget(lbl_desc)
        v_rules.addStretch()
        h_workspace.addWidget(gb_rules)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #575fcf; width: 4px; }")
        splitter.setMinimumHeight(600)
        
        w_editor = QWidget()
        v_editor = QVBoxLayout(w_editor)
        v_editor.setContentsMargins(0, 0, 0, 0)
        v_editor.addWidget(QLabel("📝 생성된 원고 텍스트 (탭을 전환하며 편집 가능):"))
        
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #747d8c; }")
        
        tab_normal = QWidget()
        v_normal = QVBoxLayout(tab_normal)
        v_normal.setContentsMargins(5, 5, 5, 5)
        self.txt_draft = QTextEdit()
        self.txt_draft.setStyleSheet("background-color: #ffffff; color: #2f3542; font-size: 13px; font-weight: normal; font-family: 'Consolas', 'Nanum Gothic';")
        self.txt_draft.setPlaceholderText("기존 스타일의 일반 초안 원고가 이곳에 생성됩니다. 직접 자유롭게 편집할 수 있습니다.")
        v_normal.addWidget(self.txt_draft)
        self.editor_tabs.addTab(tab_normal, "일반 초안 (기존 버전)")
        
        tab_seo = QWidget()
        v_seo = QVBoxLayout(tab_seo)
        v_seo.setContentsMargins(5, 5, 5, 5)
        self.txt_draft_seo = QTextEdit()
        self.txt_draft_seo.setStyleSheet("background-color: #ffffff; color: #2f3542; font-size: 13px; font-weight: normal; font-family: 'Consolas', 'Nanum Gothic';")
        self.txt_draft_seo.setPlaceholderText("SEO 최적화 규칙이 강력 강제된 초안 원고가 이곳에 생성됩니다. 직접 자유롭게 편집할 수 있습니다.")
        v_seo.addWidget(self.txt_draft_seo)
        self.editor_tabs.addTab(tab_seo, "SEO 최적화 초안 (버전 2)")
        
        v_editor.addWidget(self.editor_tabs)
        splitter.addWidget(w_editor)
        
        w_preview = QWidget()
        v_preview = QVBoxLayout(w_preview)
        v_preview.setContentsMargins(0, 0, 0, 0)
        v_preview.addWidget(QLabel("🔍 블로그 실제 출력 미리보기 (네이버 블로그 스타일):"))
        self.preview_browser = QTextBrowser()
        self.preview_browser.setReadOnly(True)
        self.preview_browser.setStyleSheet("background-color: #ffffff; border: 1px solid #747d8c; border-radius: 4px; color: #333333;")
        v_preview.addWidget(self.preview_browser)
        splitter.addWidget(w_preview)
        
        splitter.setSizes([450, 450])
        h_workspace.addWidget(splitter)
        v.addLayout(h_workspace)
        
        self.txt_draft.textChanged.connect(self.update_preview)
        self.txt_draft_seo.textChanged.connect(self.update_preview)
        self.editor_tabs.currentChanged.connect(self.update_preview)
        
        self.btn_goto_grader = QPushButton("📐 원고 검토 완료! 5단계 채점언니 SEO 분석으로 이동 👉")
        self.btn_goto_grader.setStyleSheet("background-color: #10ac84; font-size: 14px; height: 40px;")
        self.btn_goto_grader.setEnabled(True)
        self.btn_goto_grader.clicked.connect(self.goto_grader_tab)
        v.addWidget(self.btn_goto_grader)
        
        scroll_layout.addWidget(gb)
        scroll.setWidget(scroll_content)
        return scroll

    def goto_copywriter_tab(self):
        self.tabs.setCurrentIndex(4)

    def trigger_writing_pipeline(self, mode):
        self.tabs.setCurrentIndex(4)
        self.on_write_start(mode, draft_type="both")

    def on_local_ai_test(self):
        on_local_ai_test_clicked(self)

    def on_write_start(self, write_mode="blog", feedback_report=None, previous_draft=None, draft_type="both"):
        for btn in [self.btn_write_blog_normal, self.btn_write_blog_seo, self.btn_write_cafe_normal, self.btn_write_cafe_seo, self.btn_local_ai_test]:
            btn.setEnabled(False)
        self.console_copywriter.clear()
        
        active_tab_idx = self.editor_tabs.currentIndex() if hasattr(self, "editor_tabs") else 0
        mode_korean = "블로그용" if write_mode == "blog" else "카페용"
        
        if feedback_report and previous_draft:
            self.console_copywriter.append(f"🤖 [Grader Feedback] SEO 채점 의견을 반영하여 탭 {active_tab_idx+1} 원고 자동 재교정을 지시합니다...")
            if active_tab_idx == 1:
                self.txt_draft_seo.clear()
                self.txt_draft_seo.setPlainText("🤖 [AI 서프로 카피라이터 재교정 가동] SEO 피드백 반영 중...\n")
            else:
                self.txt_draft.clear()
                self.txt_draft.setPlainText("🤖 [AI 서프로 카피라이터 재교정 가동] 피드백 반영 중...\n")
        else:
            if draft_type == "normal":
                self.console_copywriter.append(f"🤖 [Main Agent] 서브에이전트(서프로 카피라이터)를 기동하여 {mode_korean} 일반 초안 원고 집필을 지시합니다...")
                self.txt_draft.clear()
                self.txt_draft.setPlainText(f"🤖 [AI 서프로 카피라이터 집필 가동] {mode_korean} 일반 원고 작성을 시작합니다...\n")
                if hasattr(self, "editor_tabs"):
                    self.editor_tabs.setCurrentIndex(0)
            elif draft_type == "seo":
                self.console_copywriter.append(f"🤖 [Main Agent] 서브에이전트(서프로 카피라이터)를 기동하여 {mode_korean} SEO 최적화 초안 원고 집필을 지시합니다...")
                self.txt_draft_seo.clear()
                self.txt_draft_seo.setPlainText(f"🤖 [AI 서프로 카피라이터 집필 가동] {mode_korean} SEO 최적화 원고 작성을 시작합니다...\n")
                if hasattr(self, "editor_tabs"):
                    self.editor_tabs.setCurrentIndex(1)
            else:
                self.console_copywriter.append(f"🤖 [Main Agent] 서브에이전트(서프로 카피라이터)를 기동하여 {mode_korean} 일반 및 SEO 최적화 원고 집필을 지시합니다...")
                self.txt_draft.clear()
                self.txt_draft.setPlainText(f"🤖 [AI 서프로 카피라이터 집필 가동] {mode_korean} 일반 원고 작성을 시작합니다...\n")
                self.txt_draft_seo.clear()
                self.txt_draft_seo.setPlainText(f"🤖 [AI 서프로 카피라이터 집필 가동] {mode_korean} SEO 최적화 원고 작성을 시작합니다...\n")
        
        QApplication.processEvents()
 
        zone_name = self.cb_zone.currentText()
        zone_num = zone_name.split()[-1].replace("구역", "")
 
        atcl_info = {
            'address': self.ent_address.text(),
            'status_main': self.ent_status_main.text(),
            'status_sub': self.ent_status_sub.text(),
            'p_sale': self.ent_sale.text(),
            'p_premium': self.ent_premium.text(),
            'invest_price': self.ent_invest.text(),
            'p_rights': self.ent_rights.text(),
            'p_rent': self.ent_rent.text(),
            'p_total': self.ent_total_buy.text(),
            'p_margin': self.ent_margin.text(),
            'final_tax_str': self.ent_tax.text(),
            'comp_type': self.ent_prop_type.text(),
            'contact': '010.2319.0977',
        }
        for key, ent in self.detail_fields.items():
            atcl_info[key] = ent.text()
 
        self.pipeline_worker = AgentPipelineWorker(
            zone_num, atcl_info, write_mode, self.generated_images,
            feedback_report=feedback_report, previous_draft=previous_draft,
            active_tab_idx=active_tab_idx, draft_type=draft_type
        )
        self.pipeline_worker.log_signal.connect(self.on_pipeline_log)
        self.pipeline_worker.draft_ready_signal.connect(self.on_draft_ready)
        self.pipeline_worker.draft_seo_ready_signal.connect(self.on_draft_seo_ready)
        self.pipeline_worker.finished_signal.connect(self.on_pipeline_finished)
        self.pipeline_worker.finished.connect(self.on_pipeline_finished_fallback)
        self.pipeline_worker.start()

    def on_pipeline_log(self, msg):
        self.console_copywriter.append(msg)

    def on_draft_ready(self, text):
        try:
            self.txt_draft.setPlainText(text)
            self.draft_text = text
            self.btn_goto_grader.setEnabled(True)
            self.update_preview()
        except Exception as e:
            print(f"❌ [GUI Error] Error in on_draft_ready: {e}", file=sys.stderr)

    def on_draft_seo_ready(self, text):
        try:
            self.txt_draft_seo.setPlainText(text)
            self.draft_seo_text = text
            self.btn_goto_grader.setEnabled(True)
            self.update_preview()
        except Exception as e:
            print(f"❌ [GUI Error] Error in on_draft_seo_ready: {e}", file=sys.stderr)

    def get_active_draft_text(self):
        if hasattr(self, "editor_tabs") and self.editor_tabs.currentIndex() == 1:
            return self.txt_draft_seo.toPlainText()
        return self.txt_draft.toPlainText()

    def update_preview(self):
        try:
            text = self.get_active_draft_text()
            html = self.render_markdown_to_naver_html(text)
            self.preview_browser.setHtml(html)
        except Exception as e:
            print(f"❌ [GUI Error] Error in update_preview: {e}", file=sys.stderr)

    def on_pipeline_finished(self):
        for btn in [self.btn_write_blog_normal, self.btn_write_blog_seo, self.btn_write_cafe_normal, self.btn_write_cafe_seo, self.btn_local_ai_test]:
            btn.setEnabled(True)
        QMessageBox.information(self, "집필 완료", "카피라이팅 초안 작성이 완료되었습니다! 원고를 보완하시거나 5단계 채점언니 단계로 진행하십시오.")

    def on_pipeline_finished_fallback(self):
        for btn in [self.btn_write_blog_normal, self.btn_write_blog_seo, self.btn_write_cafe_normal, self.btn_write_cafe_seo, self.btn_local_ai_test]:
            btn.setEnabled(True)
