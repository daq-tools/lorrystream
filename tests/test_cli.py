from click.testing import CliRunner

from lorrystream.cli import cli


def test_info():
    """
    CLI test: Invoke `lorry info`
    """
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="info",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
