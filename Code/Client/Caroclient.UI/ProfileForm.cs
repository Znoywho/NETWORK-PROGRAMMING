using System.Windows.Forms;

namespace Caroclient.UI;

public partial class ProfileForm : Form
{
    public ProfileForm(
        string username = "Player_01",
        string playerId = "player-001",
        string rank = "Chưa xếp hạng",
        int rankPoints = 0)
    {
        InitializeComponent();
        lblUsernameValue.Text = username;
        lblPlayerIdValue.Text = playerId;
        lblRankValue.Text = rank;
        lblRankPointsValue.Text = rankPoints.ToString("N0");
    }
}
