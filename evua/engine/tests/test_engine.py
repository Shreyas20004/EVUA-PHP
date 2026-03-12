"""
Engine Test Suite
Tests AST parser, rule engine, and pipeline in isolation.
"""
import asyncio
import pytest
from ..ast_parser import PHPASTParser, find_nodes
from ..rule_engine import RuleEngine, registry
from ..models.migration_models import PHPVersion, MigrationStatus, IssueSeverity
from ..pipeline import MigrationPipeline
from ..utils.version_detector import detect_version
from ..utils.diff_generator import generate_diff


# =============================================================================
# AST Parser Tests
# =============================================================================

class TestASTParser:

    def test_parses_function(self):
        src = "<?php\nfunction hello(string $name): string {\n    return 'hi';\n}"
        parser = PHPASTParser(src)
        ast = parser.parse()
        funcs = find_nodes(ast, "function_declaration")
        assert len(funcs) == 1
        assert funcs[0].metadata["name"] == "hello"
        assert funcs[0].metadata["return_type"] == "string"

    def test_parses_class(self):
        src = "<?php\nclass Foo extends Bar implements Baz {\n}"
        parser = PHPASTParser(src)
        ast = parser.parse()
        classes = find_nodes(ast, "class_declaration")
        assert len(classes) == 1
        assert classes[0].metadata["name"] == "Foo"
        assert "Bar" in classes[0].metadata["extends"]
        assert "Baz" in classes[0].metadata["implements"]

    def test_parses_namespace(self):
        src = "<?php\nnamespace App\\Services;"
        parser = PHPASTParser(src)
        ast = parser.parse()
        ns_nodes = find_nodes(ast, "namespace")
        assert len(ns_nodes) == 1

    def test_parses_if_else(self):
        src = "<?php\nif ($x > 0) {\n    echo 'yes';\n} else {\n    echo 'no';\n}"
        parser = PHPASTParser(src)
        ast = parser.parse()
        ifs = find_nodes(ast, "if_statement")
        assert len(ifs) == 1

    def test_parses_try_catch(self):
        src = "<?php\ntry {\n    doSomething();\n} catch (Exception $e) {\n    log($e);\n}"
        parser = PHPASTParser(src)
        ast = parser.parse()
        tries = find_nodes(ast, "try_statement")
        assert len(tries) == 1

    def test_empty_source(self):
        parser = PHPASTParser("<?php")
        ast = parser.parse()
        assert ast.node_type == "program"

    def test_handles_comments(self):
        src = "<?php\n// This is a comment\n/* block comment */\necho 'hi';"
        parser = PHPASTParser(src)
        ast = parser.parse()
        comments = find_nodes(ast, "comment")
        assert len(comments) >= 2


# =============================================================================
# Rule Engine Tests
# =============================================================================

class TestRuleEngine:

    def _run(self, source: str, src_ver: PHPVersion, tgt_ver: PHPVersion):
        engine = RuleEngine(dry_run=False)
        parser = PHPASTParser(source)
        ast = parser.parse()
        return engine.run("test.php", source, ast, src_ver, tgt_ver)

    def test_detects_mysql_ext(self):
        src = "<?php\n$conn = mysql_connect('localhost', 'user', 'pass');"
        result = self._run(src, PHPVersion.PHP_5_6, PHPVersion.PHP_8_0)
        rule_ids = [m.rule_id for m in result.rule_matches]
        assert "PHP56_MYSQL_EXT" in rule_ids

    def test_fixes_ereg(self):
        src = "<?php\n$m = ereg('pattern', $str);"
        result = self._run(src, PHPVersion.PHP_5_6, PHPVersion.PHP_7_0)
        assert "ereg(" not in result.migrated_code
        assert "preg_match(" in result.migrated_code

    def test_fixes_split(self):
        src = "<?php\n$parts = split(',', $str);"
        result = self._run(src, PHPVersion.PHP_5_6, PHPVersion.PHP_7_0)
        assert "split(" not in result.migrated_code
        assert "preg_split(" in result.migrated_code

    def test_fixes_magic_quotes(self):
        src = "<?php\n$gpc = get_magic_quotes_gpc();"
        result = self._run(src, PHPVersion.PHP_5_6, PHPVersion.PHP_7_0)
        assert "false" in result.migrated_code

    def test_ai_required_for_mysql(self):
        src = "<?php\n$res = mysql_query($sql);"
        result = self._run(src, PHPVersion.PHP_5_6, PHPVersion.PHP_8_0)
        assert result.status == MigrationStatus.AI_REQUIRED

    def test_no_matches_clean_code(self):
        src = "<?php\ndeclare(strict_types=1);\n$x = 42;\necho $x;"
        result = self._run(src, PHPVersion.PHP_8_0, PHPVersion.PHP_8_2)
        assert result.status in (MigrationStatus.COMPLETED, MigrationStatus.RULE_APPLIED)

    def test_severity_critical_mysql(self):
        src = "<?php\nmysql_connect();"
        result = self._run(src, PHPVersion.PHP_5_6, PHPVersion.PHP_7_0)
        critical = [i for i in result.issues if i.severity == IssueSeverity.CRITICAL]
        assert len(critical) >= 1

    def test_dry_run_no_changes(self):
        src = "<?php\n$m = ereg('x', $s);"
        engine = RuleEngine(dry_run=True)
        parser = PHPASTParser(src)
        ast = parser.parse()
        result = engine.run("test.php", src, ast, PHPVersion.PHP_5_6, PHPVersion.PHP_7_0)
        # Dry run: source unchanged despite auto_fixable match
        assert result.migrated_code == src

    def test_create_function_needs_ai(self):
        src = "<?php\n$fn = create_function('$x', 'return $x * 2;');"
        result = self._run(src, PHPVersion.PHP_7_4, PHPVersion.PHP_8_0)
        assert any(m.rule_id == "PHP7X_CREATE_FUNCTION" for m in result.rule_matches)
        assert result.status == MigrationStatus.AI_REQUIRED

    def test_stats_populated(self):
        src = "<?php\nmysql_connect();\nereg('x', $s);"
        result = self._run(src, PHPVersion.PHP_5_6, PHPVersion.PHP_8_0)
        assert "total_matches" in result.stats
        assert result.stats["total_matches"] >= 2


# =============================================================================
# Version Detector Tests
# =============================================================================

class TestVersionDetector:

    def test_detects_legacy_mysql(self):
        src = "<?php\n$c = mysql_connect('localhost', 'root', '');"
        assert detect_version(src) == PHPVersion.PHP_5_6

    def test_detects_php8_match(self):
        src = "<?php\n$r = match($x) { 1 => 'one', default => 'other' };"
        assert detect_version(src) == PHPVersion.PHP_8_0

    def test_detects_php81_enum(self):
        src = "<?php\nenum Status { case Active; case Inactive; }"
        assert detect_version(src) == PHPVersion.PHP_8_1

    def test_detects_php74_arrow_fn(self):
        src = "<?php\n$fn = fn($x) => $x * 2;"
        assert detect_version(src) == PHPVersion.PHP_7_4


# =============================================================================
# Diff Generator Tests
# =============================================================================

class TestDiffGenerator:

    def test_produces_diff(self):
        original = "<?php\nmysql_connect();\n"
        migrated = "<?php\nmysqli_connect();\n"
        diff = generate_diff(original, migrated, "test.php")
        assert "-mysql_connect" in diff
        assert "+mysqli_connect" in diff

    def test_no_diff_identical(self):
        src = "<?php\necho 'hello';\n"
        diff = generate_diff(src, src, "test.php")
        assert diff == ""


# =============================================================================
# Pipeline Integration Tests
# =============================================================================

class TestMigrationPipeline:

    def _pipeline(self):
        return MigrationPipeline(
            source_version=PHPVersion.PHP_5_6,
            target_version=PHPVersion.PHP_8_0,
            use_mock_ai=True,
        )

    def test_run_single_file(self, tmp_path):
        php = tmp_path / "test.php"
        php.write_text("<?php\n$conn = mysql_connect('localhost', 'u', 'p');\n")
        pipeline = self._pipeline()
        result = pipeline.run_file(str(php))
        assert result.status != MigrationStatus.FAILED
        assert result.file_path == str(php)

    def test_run_directory(self, tmp_path):
        (tmp_path / "a.php").write_text("<?php\n$x = ereg('p', $s);\n")
        (tmp_path / "b.php").write_text("<?php\n$y = split(',', $s);\n")
        pipeline = self._pipeline()
        pr = pipeline.run_directory(str(tmp_path))
        assert pr.total_files == 2
        assert pr.completed + pr.failed == 2

    def test_output_written(self, tmp_path):
        src_dir = tmp_path / "src"
        out_dir = tmp_path / "out"
        src_dir.mkdir()
        (src_dir / "app.php").write_text("<?php\n$x = split(',', $s);\n")
        pipeline = self._pipeline()
        pipeline.run_directory(str(src_dir), output_dir=str(out_dir))
        assert (out_dir / "app.php").exists()

    def test_async_single_file(self, tmp_path):
        php = tmp_path / "async_test.php"
        php.write_text("<?php\necho 'hello';\n")
        pipeline = self._pipeline()
        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run_file_async(str(php))
        )
        assert result.status == MigrationStatus.COMPLETED

    def test_skips_vendor_directory(self, tmp_path):
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / "lib.php").write_text("<?php\n// vendor file\n")
        (tmp_path / "app.php").write_text("<?php\necho 'app';\n")
        pipeline = self._pipeline()
        pr = pipeline.run_directory(str(tmp_path))
        assert pr.total_files == 1  # vendor excluded
