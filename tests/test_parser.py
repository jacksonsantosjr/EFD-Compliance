# -*- coding: utf-8 -*-
"""
Testes unitários do parser SPED EFD com arquivo real KAWAPOLPA.
Arquivo: SpedEFD-58274111000176-151751101115-Remessa de arquivo original-mar.2026.txt
"""
import sys
import os
from pathlib import Path
from decimal import Decimal

# Adicionar raiz do projeto ao path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from parser.registro import Registro
from parser.layout_detector import detect_layout_version, get_version_family
from parser.sped_parser import parse_sped_file, SpedParseResult

# Fixture path
FIXTURE_FILE = Path(__file__).parent / "SpedEFD-58274111000176-151751101115-Remessa de arquivo original-mar.2026.txt"


class TestRegistro:
    """Testa a classe base Registro."""

    def test_parse_linha_basica(self):
        linha = "|0000|020|0|01032026|31032026|KAWAPOLPA EMBALAGENS LTDA|58274111000176||SP|151751101115|3550308|||A|0|"
        reg = Registro(linha, 1)
        assert reg.reg == "0000"
        assert reg.campos_raw[0] == "0000"
        assert reg.campos_raw[5] == "KAWAPOLPA EMBALAGENS LTDA"
        assert reg.total_campos() == 15

    def test_get_campo_decimal(self):
        linha = "|E110|0|0|9879,02|0|39544,23|0|5229,31|0|106394,51|0|0|0|141289,03|0|"
        reg = Registro(linha, 1)
        reg.CAMPOS = {"VL_TOT_AJ_DEBITOS": 3, "VL_TOT_CREDITOS": 5}
        assert reg.get_campo_decimal("VL_TOT_AJ_DEBITOS") == Decimal("9879.02")
        assert reg.get_campo_decimal("VL_TOT_CREDITOS") == Decimal("39544.23")

    def test_get_campo_int(self):
        linha = "|9999|450|"
        reg = Registro(linha, 1)
        reg.CAMPOS = {"QTD_LIN": 1}
        assert reg.get_campo_int("QTD_LIN") == 450

    def test_get_campo_date(self):
        linha = "|0000|020|0|01032026|31032026|"
        reg = Registro(linha, 1)
        reg.CAMPOS = {"DT_INI": 3, "DT_FIN": 4}
        dt = reg.get_campo_date("DT_INI")
        assert dt is not None
        assert dt.day == 1
        assert dt.month == 3
        assert dt.year == 2026

    def test_campo_vazio_retorna_zero(self):
        linha = "|G125|13|01032026|IM|1093,84||||1|22,79|"
        reg = Registro(linha, 1)
        reg.CAMPOS = {"VL_IMOB_ICMS_ST": 5, "VL_IMOB_ICMS_FRT": 6, "VL_IMOB_ICMS_DIF": 7}
        assert reg.get_campo_decimal("VL_IMOB_ICMS_ST") == Decimal("0")
        assert reg.get_campo_decimal("VL_IMOB_ICMS_FRT") == Decimal("0")

    def test_to_dict(self):
        linha = "|0001|0|"
        reg = Registro(linha, 5)
        reg.CAMPOS = {"REG": 0, "IND_MOV": 1}
        d = reg.to_dict()
        assert d["REG"] == "0001"
        assert d["IND_MOV"] == "0"
        assert d["_linha"] == 5


class TestLayoutDetector:
    """Testa a detecção de versão do layout."""

    def test_detect_version_020(self):
        assert detect_layout_version("020") == "3.2.1"

    def test_detect_version_021(self):
        assert detect_layout_version("021") == "3.2.2"

    def test_detect_version_unknown(self):
        assert detect_layout_version("999") is None

    def test_version_family_020(self):
        assert get_version_family("020") == "v3_2"

    def test_version_family_013(self):
        assert get_version_family("013") == "v3_1"

    def test_version_family_fallback(self):
        assert get_version_family("999") == "v3_2"


class TestSpedParser:
    """Testa o parser principal com o arquivo real KAWAPOLPA."""

    @classmethod
    def setup_class(cls):
        """Carrega o arquivo SPED uma única vez para todos os testes."""
        assert FIXTURE_FILE.exists(), f"Fixture não encontrada: {FIXTURE_FILE}"
        cls.parsed = parse_sped_file(FIXTURE_FILE)

    def test_file_info_cnpj(self):
        assert self.parsed.file_info.cnpj == "58274111000176"

    def test_file_info_nome(self):
        assert self.parsed.file_info.nome == "KAWAPOLPA EMBALAGENS LTDA"

    def test_file_info_uf(self):
        assert self.parsed.file_info.uf == "SP"

    def test_file_info_ie(self):
        assert self.parsed.file_info.ie == "151751101115"

    def test_file_info_perfil(self):
        assert self.parsed.file_info.ind_perfil == "A"

    def test_file_info_cod_ver(self):
        assert self.parsed.file_info.cod_ver == "020"
        assert self.parsed.file_info.layout_version == "3.2.1"

    def test_file_info_periodo(self):
        assert self.parsed.file_info.dt_ini is not None
        assert self.parsed.file_info.dt_ini.month == 3
        assert self.parsed.file_info.dt_ini.year == 2026
        assert self.parsed.file_info.dt_fin.day == 31

    def test_file_info_atividade(self):
        assert self.parsed.file_info.ind_ativ == "0"  # Industrial

    def test_total_linhas(self):
        """O 9999 declara 450 linhas."""
        reg_9999 = self.parsed.get_registro_unico("9999")
        assert reg_9999 is not None
        qtd = reg_9999.get_campo_int("QTD_LIN")
        assert qtd == 450

    def test_encoding_detected(self):
        assert self.parsed.encoding_used in ("latin-1", "utf-8", "cp1252")

    def test_file_hash_not_empty(self):
        assert len(self.parsed.file_hash) == 64  # SHA-256

    def test_bloco_0_exists(self):
        bloco_0 = self.parsed.get_bloco("0")
        assert len(bloco_0) > 0
        assert "0000" in bloco_0

    def test_bloco_c_exists(self):
        bloco_c = self.parsed.get_bloco("C")
        assert "C100" in bloco_c
        assert "C190" in bloco_c

    def test_c100_count(self):
        """9900 declara 10 registros C100."""
        c100 = self.parsed.get_registros("C100")
        assert len(c100) == 10

    def test_c190_count(self):
        """9900 declara 15 registros C190."""
        c190 = self.parsed.get_registros("C190")
        assert len(c190) == 15

    def test_c170_count(self):
        """9900 declara 129 registros C170."""
        c170 = self.parsed.get_registros("C170")
        assert len(c170) == 129

    def test_e110_exists(self):
        e110 = self.parsed.get_registro_unico("E110")
        assert e110 is not None

    def test_e110_values(self):
        """Verifica valores reais do E110:
        |E110|0|0|9879,02|0|39544,23|0|5229,31|0|106394,51|0|0|0|141289,03|0|
        """
        e110 = self.parsed.get_registro_unico("E110")
        assert e110.get_campo_decimal("VL_TOT_DEBITOS") == Decimal("0")
        assert e110.get_campo_decimal("VL_AJ_DEBITOS") == Decimal("0")
        assert e110.get_campo_decimal("VL_TOT_AJ_DEBITOS") == Decimal("9879.02")
        assert e110.get_campo_decimal("VL_TOT_CREDITOS") == Decimal("39544.23")
        assert e110.get_campo_decimal("VL_TOT_AJ_CREDITOS") == Decimal("5229.31")
        assert e110.get_campo_decimal("VL_SLD_CREDOR_ANT") == Decimal("106394.51")
        assert e110.get_campo_decimal("VL_ICMS_RECOLHER") == Decimal("0")
        assert e110.get_campo_decimal("VL_SLD_CREDOR_TRANSPORTAR") == Decimal("141289.03")

    def test_e111_count(self):
        """9900 declara 2 registros E111."""
        e111 = self.parsed.get_registros("E111")
        assert len(e111) == 2

    def test_e111_codes_sao_sp(self):
        """Ambos E111 devem ter códigos com prefixo SP."""
        e111_list = self.parsed.get_registros("E111")
        for e111 in e111_list:
            cod = e111.get_campo("COD_AJ_APUR")
            assert cod.startswith("SP"), f"Código {cod} não começa com SP"

    def test_e111_sp000207(self):
        """E111 SP000207 = 9879,02 (débito ajuste)."""
        e111_list = self.parsed.get_registros("E111")
        sp000207 = [e for e in e111_list if e.get_campo("COD_AJ_APUR") == "SP000207"]
        assert len(sp000207) == 1
        assert sp000207[0].get_campo_decimal("VL_AJ_APUR") == Decimal("9879.02")

    def test_e520_ipi(self):
        """E520: |E520|1668,18|0|6709,12|0|0|8377,3|0|"""
        e520 = self.parsed.get_registro_unico("E520")
        assert e520 is not None
        assert e520.get_campo_decimal("VL_SD_ANT_IPI") == Decimal("1668.18")
        assert e520.get_campo_decimal("VL_CRED_IPI") == Decimal("6709.12")
        assert e520.get_campo_decimal("VL_SC_IPI") == Decimal("8377.30")

    def test_g110_exists(self):
        g110 = self.parsed.get_registro_unico("G110")
        assert g110 is not None

    def test_g110_values(self):
        """G110: |G110|01032026|31032026|106394,01|2445,15|0|0|0|0|0|"""
        g110 = self.parsed.get_registro_unico("G110")
        assert g110.get_campo_decimal("SALDO_IN_ICMS") == Decimal("106394.01")
        assert g110.get_campo_decimal("SOM_PARC") == Decimal("2445.15")
        assert g110.get_campo_decimal("VL_TRIB_EXP") == Decimal("0")
        assert g110.get_campo_decimal("ICMS_APROP") == Decimal("0")

    def test_g125_count(self):
        """9900 declara 16 registros G125."""
        g125 = self.parsed.get_registros("G125")
        assert len(g125) == 16

    def test_g125_tipos_movimentacao(self):
        """Deve ter registros SI (saldo inicial) e IM (imobilização)."""
        g125_list = self.parsed.get_registros("G125")
        tipos = {g.get_campo("TIPO_MOV") for g in g125_list}
        assert "SI" in tipos
        assert "IM" in tipos

    def test_g140_count(self):
        g140 = self.parsed.get_registros("G140")
        assert len(g140) == 4

    def test_0200_count(self):
        """9900 declara 113 registros 0200."""
        r0200 = self.parsed.get_registros("0200")
        assert len(r0200) == 113

    def test_0150_count(self):
        """9900 declara 8 registros 0150."""
        r0150 = self.parsed.get_registros("0150")
        assert len(r0150) == 8

    def test_0300_count(self):
        """9900 declara 16 registros 0300."""
        r0300 = self.parsed.get_registros("0300")
        assert len(r0300) == 16

    def test_bloco_d_sem_movimento(self):
        d001 = self.parsed.get_registro_unico("D001")
        if d001:
            assert d001.get_campo("IND_MOV") == "1"  # Sem movimento

    def test_bloco_k_sem_movimento(self):
        k001 = self.parsed.get_registro_unico("K001")
        if k001:
            assert k001.get_campo("IND_MOV") == "1"

    def test_bloco_h_sem_movimento(self):
        h001 = self.parsed.get_registro_unico("H001")
        if h001:
            assert h001.get_campo("IND_MOV") == "1"

    def test_get_registro_unico_inexistente(self):
        assert self.parsed.get_registro_unico("E210") is None

    def test_get_registros_inexistente(self):
        assert self.parsed.get_registros("X999") == []

    def test_total_registros(self):
        """Total de registros deve ser > 0."""
        assert self.parsed.total_registros > 400

    def test_no_parse_errors(self):
        """O arquivo válido (pós-PVA) não deve ter erros de parse."""
        assert len(self.parsed.erros_parse) == 0


# --- Runnable ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print(" EFD Compliance - Testes Unitarios do Parser")
    print(" Fixture: " + FIXTURE_FILE.name)
    print("="*60 + "\n")

    # Init TestSpedParser
    if FIXTURE_FILE.exists():
        TestSpedParser.setup_class()

    passed = 0
    failed = 0
    errors = []

    for test_class in [TestRegistro, TestLayoutDetector, TestSpedParser]:
        print("\n--- " + test_class.__name__ + " ---")
        instance = test_class()
        if hasattr(test_class, 'parsed'):
            instance.parsed = test_class.parsed

        for name in sorted(dir(test_class)):
            if not name.startswith("test_"):
                continue
            try:
                getattr(instance, name)()
                print("  [PASS] " + name)
                passed += 1
            except AssertionError as e:
                print("  [FAIL] " + name + ": " + str(e))
                failed += 1
                errors.append((test_class.__name__, name, str(e)))
            except Exception as e:
                print("  [ERR]  " + name + ": " + type(e).__name__ + ": " + str(e))
                failed += 1
                errors.append((test_class.__name__, name, type(e).__name__ + ": " + str(e)))

    print("\n" + "="*60)
    print(" Resultado: %d passaram, %d falharam" % (passed, failed))
    print("="*60)

    if errors:
        print("\nFalhas:")
        for cls, name, err in errors:
            print("  %s.%s: %s" % (cls, name, err))

    sys.exit(1 if failed > 0 else 0)

