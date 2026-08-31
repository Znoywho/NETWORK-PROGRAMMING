using System;
using System.Collections.Generic;
using System.Text;

namespace Caroclient.UI
{
    public class Player
    {
        private string name; // Ctrl + R = E (sinh ra đóng gói)

        public string Name { get => name; set => name = value; }

        private Image mark;
        public Image Mark { get => mark; set => mark = value; }

        public Player(string name, Image mark)
        {
            this.Name = name;
            this.Mark = mark;
        }
    }

}
