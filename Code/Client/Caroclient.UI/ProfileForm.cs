using System.Windows.Forms;

namespace Caroclient.UI;

public partial class ProfileForm : Form
{
    public ProfileForm(
        string username = "Player_01",
        string playerId = "player-001",
        int points = 0)
    {
        InitializeComponent();
        lblUsernameValue.Text = username;
        lblPlayerIdValue.Text = playerId;
        lblRankPointsValue.Text = points.ToString("N0");
    }
}
