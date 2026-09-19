namespace Caroclient.UI;

public partial class AccountForm : Form
{
    public AccountForm(string username = "Player_01", string playerId = "player-001")
    {
        InitializeComponent();
        txtUsername.Text = username;
        txtPlayerId.Text = playerId;
    }
}
